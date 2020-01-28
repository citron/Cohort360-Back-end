import coreapi
import coreschema
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView

from cohort_back.settings import VOTING_GITLAB
from voting.models import Vote


def req_url(method, end):
    url = VOTING_GITLAB['api_url'] + "/projects/" + VOTING_GITLAB['project_name'] + end
    print(url)
    return getattr(requests, method)(
        url,
        headers={"PRIVATE-TOKEN": VOTING_GITLAB['private_token']})


class Voting(APIView):
    permission_classes = (IsAuthenticated,)

    get_schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "per_page",
            required=True,
            location="per_page",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "page",
            required=True,
            location="page",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "state",
            required=False,
            location="state",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "labels",
            required=True,
            location="labels",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "milestone",
            required=False,
            location="milestone",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "iids[]",
            required=False,
            location="iids[]",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "author_id",
            required=False,
            location="author_id",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "assignee_id",
            required=False,
            location="assignee_id",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "my_reaction_emoji",
            required=False,
            location="my_reaction_emoji",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "search",
            required=False,
            location="search",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "confidential",
            required=False,
            location="confidential",
            schema=coreschema.Boolean()
        ),
    ])

    def get(self, request):
        """
        Return a list of gitlab issues. Please refer to https://docs.gitlab.com/ee/api/issues.html for parameters.
        """
        self.schema = Voting.get_schema

        allowed_params = ['per_page', 'page', 'state', 'labels', 'milestone', 'iids[]', 'author_id', 'assignee_id',
                          'my_reaction_emoji', 'search', 'confidential', 'order_by', 'sort', 'created_after',
                          'created_before', 'updated_after', 'updated_before']
        params = []

        if 'per_page' not in request.query_params \
                or 'page' not in request.query_params \
                or 'labels' not in request.query_params:
            return Response({'error': 'per_page, page and labels parameters required!'},
                            status=status.HTTP_400_BAD_REQUEST)

        for allowed_param in allowed_params:
            if allowed_param in request.query_params:
                if allowed_param == 'labels':
                    for l in request.query_params['labels'].split(','):
                        if l not in VOTING_GITLAB['authorized_labels']:
                            return Response({'error': 'label "{}" not authorized! Authorized labels are: "{}"'.format(
                                l, ','.join(VOTING_GITLAB['authorized_labels']))}, status=status.HTTP_400_BAD_REQUEST)

                params.append('{}={}'.format(allowed_param, request.query_params[allowed_param]))

        res = req_url("get", "/issues?{}".format('&'.join(params)))
        if res.status_code != 200:
            return Response({"Internal": ["Error {} while contacting gitlab server!".format(res.status_code)],
                             "contents": res.text},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        result = res.json()
        return Response(result)

    post_schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "title",
            required=True,
            location="title",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "description",
            required=True,
            location="description",
            schema=coreschema.String()
        ),
    ])

    def post(self, request):
        """
        Post a new issue. This issue is either a bug or a feature request, and will be added in corresponding columns in gitlab.
        The posted data must contains a title and a description.
        """
        self.schema = Voting.post_schema

        if 'title' not in request.data or 'description' not in request.data:
            return Response({'error': 'missing title or description in the POST request'},
                            status=status.HTTP_400_BAD_REQUEST)

        title = request.data['title']
        description = request.data['description']



        return


class Thumbs(APIView):
    permission_classes = (IsAuthenticated,)

    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "issue_id",
            required=True,
            location="issue_id",
            schema=coreschema.Integer()
        ),
        coreapi.Field(
            "vote",
            required=True,
            location="vote",
            schema=coreschema.Integer()
        ),
    ])

    def post(self, request):
        if 'issue_id' not in request.data or 'vote' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            issue_id = int(request.data['issue_id'])
            if issue_id < 0:
                raise ValueError()
        except ValueError:
            return Response({'error': 'issue_id is not a valid positive integer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vote_value = int(request.data['vote'])
            if vote_value not in [-1, 0, 1]:
                raise ValueError()
        except ValueError:
            return Response({'error': 'vote should be either -1, 0 or 1'}, status=status.HTTP_400_BAD_REQUEST)

        vote = Vote.objects.get_or_create(issue_id=issue_id, user=request.user)[0]
        vote.vote = vote_value
        vote.save()

        issue_neg = Vote.objects.filter(issue_id=issue_id, vote=-1).aggregate(Sum('vote'))
        issue_neg = issue_neg['vote__sum'] if issue_neg['vote__sum'] is not None else 0
        issue_pos = Vote.objects.filter(issue_id=issue_id, vote=1).aggregate(Sum('vote'))
        issue_pos = issue_pos['vote__sum'] if issue_pos['vote__sum'] is not None else 0
        issue_total = issue_pos + issue_neg
        return Response({'issue_id': issue_id,
                         'thumbs_total': issue_total,
                         'thumbs_positive': issue_pos,
                         'thumbs_negative': issue_neg})
