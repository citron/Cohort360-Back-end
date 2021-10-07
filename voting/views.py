from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cohort.models import User
from cohort_back.serializers import ErrorSerializer
from cohort_back.settings import VOTING_ATTACHMENT_MAX_SIZE, VOTING_POST_LABELS
from voting.serializers import IssuePostSerializer, ApiIssueSerializer
import voting.util as gitlab
from voting.util import AttachmentReturned

# fields = (
#     "iid", "state", "labels", "gitlab_created_at", "gitlab_updated_at",
#     "gitlab_closed_at", "title", "description", "votes_positive_sum",
#     "votes_neutral_sum", "votes_negative_sum", "votes_total_sum",
# )

# class GitlabIssueViewSet(BaseViewSet):
#     filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,
#                        ContainsFilter, ListContainsFilter)
#
#     queryset = GitlabIssue.objects.all()
#     serializer_class = GitlabIssueSerializer
#     http_method_names = ['get']
#
#     filterset_fields = ('iid', 'state', 'labels', 'title')
#     ordering_fields = ('iid', 'state', 'gitlab_created_at', 'gitlab_updated_at', 'gitlab_closed_at',
#                        'votes_positive_sum', 'votes_neutral_sum', 'votes_negative_sum', 'votes_total_sum',)
#     ordering = ('-votes_total_sum',)
#     search_fields = ['title', 'description', 'labels']
#     contains_fields = ['title', 'description']
#     list_contains_fields = ['labels']


def build_error_message(status_code: int, msg: str) -> str:
    return f"Error {status_code} while contacting gitlab server : {msg}"


def build_full_description(description: str, user: User, markdown: str) -> str:
    return f"{description}\n\nEnvoyée par " \
           f"{user.displayname or 'Unknown'} ({user.email}) " \
           + (
               f"\n\nAttachment: {markdown}\nPar sécurité, vérifier que vous" \
               f" ayez un antivirus à jour avant tout téléchargement"
               if markdown else ""
           )


class IssuePost(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = IssuePostSerializer
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "label", openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description=f"Can be one of "
                            f"{', '.join(VOTING_POST_LABELS)}"
            ),
        ],
        responses={
            201: openapi.Response('Success', ApiIssueSerializer),
            400: openapi.Response('Invalid data', ErrorSerializer),
            403: openapi.Response('Not authenticated'),
            500: openapi.Response('Error within connection to Gitlab server',
                                  ErrorSerializer)
        },
    )
    def post(self, request):
        """
        Post a new issue. This issue is either a bug or a feature request, and
        will be added in corresponding columns in gitlab. The posted data must
        contains a single label, a title and a description.
        """
        for field in ['title', 'description', 'label']:
            if field not in request.data:
                return Response(
                    {'error': f'missing {field} in the POST request'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        title = request.data['title']
        description = request.data['description']
        label = request.data['label']
        attach = request.data.get('attachment', None)
        markdown = ""

        if label not in VOTING_POST_LABELS:
            return Response(
                {
                    'message': f'label "{label}" not authorized, choices are: '
                               f'{",".join(VOTING_POST_LABELS)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(description) == 0:
            return Response({'message': 'title ou description empty'},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(title) == 0:
            return Response({'message': 'title ou description empty'},
                            status=status.HTTP_400_BAD_REQUEST)
        if attach:
            if attach.size > VOTING_ATTACHMENT_MAX_SIZE:  # 10Mo
                return Response({
                    'message': f"Le fichier joint doit être de taille "
                               f"inférieure à "
                               f"{VOTING_ATTACHMENT_MAX_SIZE / 10 ** 6}Mo"
                }, status=status.HTTP_400_BAD_REQUEST
                )
            attach_res = gitlab.post_gitlab_attachment(file=attach)
            if attach_res.status_code != status.HTTP_201_CREATED:
                return Response(ErrorSerializer({
                    "message": build_error_message(
                        attach_res.status_code, attach_res.text
                    ),
                }).data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            gitlab_attachment = AttachmentReturned(resp=attach_res)
            markdown = gitlab_attachment.markdown

        res = gitlab.post_gitlab_issue(data={
            'title': title,
            'description': build_full_description(
                description=description, user=request.user, markdown=markdown
            ),
            'labels': [label]
        })
        if res.status_code != 201:
            return Response(ErrorSerializer({
                "message": build_error_message(res.status_code, res.text),
            }).data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            ApiIssueSerializer(res.json()).data, status=status.HTTP_201_CREATED
        )


# class Thumbs(GenericAPIView):
#     permission_classes = (IsAuthenticated,)
#     serializer_class = ThumbSerializer
#
#     def post(self, request):
#         if 'issue_iid' not in request.data or 'vote' not in request.data:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#         try:
#             issue_iid = int(request.data['issue_iid'])
#             if issue_iid < 0:
#                 raise ValueError()
#         except ValueError:
#             return Response({'error': 'issue_iid is not a valid positive integer'}, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             vote_value = int(request.data['vote'])
#             if vote_value not in [-1, 0, 1]:
#                 raise ValueError()
#         except ValueError:
#             return Response({'error': 'vote should be either -1, 0 or 1'}, status=status.HTTP_400_BAD_REQUEST)
#
#         #GitlabIssue.objects.all().filter(labels__regex=)
#
#         try:
#             gi = GitlabIssue.objects.get(iid=issue_iid)
#         except GitlabIssue.DoesNotExist:
#             raise Response({'error': 'issue_iid does not match an existing gitlab issue.'},
#                            status=status.HTTP_404_NOT_FOUND)
#
#         vote = Vote.objects.get_or_create(issue=gi, user=request.user)[0]
#         vote.vote = vote_value
#         vote.save()
#
#         issue_votes = Vote.objects.filter(issue=gi)
#         gi.votes_positive_sum = issue_votes.filter(vote=1).aggregate(Sum('vote'))['vote__sum']
#         gi.votes_positive_sum = gi.votes_positive_sum if gi.votes_positive_sum else 0
#         gi.votes_neutral_sum = issue_votes.filter(vote=0).aggregate(Sum('vote'))['vote__sum']
#         gi.votes_neutral_sum = gi.votes_neutral_sum if gi.votes_neutral_sum else 0
#         gi.votes_negative_sum = issue_votes.filter(vote=-1).aggregate(Sum('vote'))['vote__sum']
#         gi.votes_negative_sum = gi.votes_negative_sum if gi.votes_negative_sum else 0
#         gi.votes_total_sum = gi.votes_positive_sum + gi.votes_negative_sum
#         gi.save()
#
#         return Response({'issue': GitlabIssueSerializer(gi, context={'request': request}).data})
