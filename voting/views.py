from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cohort.views import BaseViewSet
from cohort_back.settings import VOTING_GITLAB
from voting.celery import get_or_create_gitlab_issue
from voting.filters import ContainsFilter, ListContainsFilter
from voting.models import Vote, GitlabIssue
from voting.serializers import GitlabIssueSerializer, IssuePostSerializer, ThumbSerializer
from voting.util import req_url


fields = ("iid", "state", 'labels',
          "gitlab_created_at", "gitlab_updated_at", "gitlab_closed_at",
          "title", "description",
          "votes_positive_sum", "votes_neutral_sum", "votes_negative_sum", "votes_total_sum",)


class GitlabIssueViewSet(BaseViewSet):
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter, ContainsFilter, ListContainsFilter)

    queryset = GitlabIssue.objects.all()
    serializer_class = GitlabIssueSerializer
    http_method_names = ['get']

    filterset_fields = ('iid', 'state', 'labels', 'title')
    ordering_fields = ('iid', 'state', 'gitlab_created_at', 'gitlab_updated_at', 'gitlab_closed_at',
                       'votes_positive_sum', 'votes_neutral_sum', 'votes_negative_sum', 'votes_total_sum',)
    ordering = ('-votes_total_sum',)
    search_fields = ['title', 'description', 'labels']
    contains_fields = ['title', 'description']
    list_contains_fields = ['labels']


class IssuePost(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = IssuePostSerializer

    def post(self, request):
        """
        Post a new issue. This issue is either a bug or a feature request, and will be added in corresponding columns in gitlab.
        The posted data must contains a single label, a title and a description.
        """
        if 'title' not in request.data or 'description' not in request.data or 'label' not in request.data:
            return Response({'error': 'missing label, title or description in the POST request'},
                            status=status.HTTP_400_BAD_REQUEST)

        title = request.data['title']
        description = request.data['description'] + '\n\n Sent by ' + request.user.displayname \
            if request.user.displayname else 'Unknown'
        label = request.data['label']

        if label not in VOTING_GITLAB['post_labels']:
            return Response({'error': 'label "{}" not authorized, choices are: "{}"'.format(
                label, ','.join(VOTING_GITLAB['post_labels']))},
                status=status.HTTP_400_BAD_REQUEST)

        if len(title) == 0 or len(description) == 0:
            return Response({'error': 'title or description empty!'},
                            status=status.HTTP_400_BAD_REQUEST)

        res = req_url("post", "/issues", data={'title': title, 'description': description, 'labels': label})
        if res.status_code != 201:
            return Response({"Internal": ["Error {} while contacting gitlab server!".format(res.status_code)],
                             "contents": res.text},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        gi = get_or_create_gitlab_issue(res.json())

        return Response(GitlabIssueSerializer(gi, context={'request': request}).data)


class Thumbs(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ThumbSerializer

    def post(self, request):
        if 'issue_iid' not in request.data or 'vote' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            issue_iid = int(request.data['issue_iid'])
            if issue_iid < 0:
                raise ValueError()
        except ValueError:
            return Response({'error': 'issue_iid is not a valid positive integer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vote_value = int(request.data['vote'])
            if vote_value not in [-1, 0, 1]:
                raise ValueError()
        except ValueError:
            return Response({'error': 'vote should be either -1, 0 or 1'}, status=status.HTTP_400_BAD_REQUEST)

        #GitlabIssue.objects.all().filter(labels__regex=)

        try:
            gi = GitlabIssue.objects.get(iid=issue_iid)
        except GitlabIssue.DoesNotExist:
            raise Response({'error': 'issue_iid does not match an existing gitlab issue.'},
                           status=status.HTTP_404_NOT_FOUND)

        vote = Vote.objects.get_or_create(issue=gi, user=request.user)[0]
        vote.vote = vote_value
        vote.save()

        issue_votes = Vote.objects.filter(issue=gi)
        gi.votes_positive_sum = issue_votes.filter(vote=1).aggregate(Sum('vote'))['vote__sum']
        gi.votes_positive_sum = gi.votes_positive_sum if gi.votes_positive_sum else 0
        gi.votes_neutral_sum = issue_votes.filter(vote=0).aggregate(Sum('vote'))['vote__sum']
        gi.votes_neutral_sum = gi.votes_neutral_sum if gi.votes_neutral_sum else 0
        gi.votes_negative_sum = issue_votes.filter(vote=-1).aggregate(Sum('vote'))['vote__sum']
        gi.votes_negative_sum = gi.votes_negative_sum if gi.votes_negative_sum else 0
        gi.votes_total_sum = gi.votes_positive_sum + gi.votes_negative_sum
        gi.save()

        return Response({'issue': GitlabIssueSerializer(gi, context={'request': request}).data})
