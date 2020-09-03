from rest_framework import serializers
from rest_framework.fields import Field, _UnvalidatedField

from cohort.serializers import BaseSerializer
from voting.models import GitlabIssue, Vote


class MyListField(Field):
    child = _UnvalidatedField()
    initial = []
    default_error_messages = {}

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return data.split(',')


class GitlabIssueSerializer(BaseSerializer):
    iid = serializers.IntegerField(read_only=True)
    state = serializers.CharField(read_only=True)
    labels = MyListField(read_only=True)
    gitlab_created_at = serializers.DateTimeField(read_only=True)
    gitlab_updated_at = serializers.DateTimeField(read_only=True)
    gitlab_closed_at = serializers.DateTimeField(read_only=True)

    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    votes_positive_sum = serializers.IntegerField(read_only=True)
    votes_neutral_sum = serializers.IntegerField(read_only=True)
    votes_negative_sum = serializers.IntegerField(read_only=True)
    votes_total_sum = serializers.IntegerField(read_only=True)

    user_vote = serializers.SerializerMethodField(read_only=True)

    def get_user_vote(self, gitlabissue):
        vote = Vote.objects.filter(issue=gitlabissue, user=self.context['request'].user)
        if vote.exists():
            return vote[0].vote
        else:
            return 0

    class Meta:
        model = GitlabIssue
        fields = ("iid", "state", 'labels',
                  "gitlab_created_at", "gitlab_updated_at", "gitlab_closed_at",
                  "title", "description",
                  "votes_positive_sum", "votes_neutral_sum", "votes_negative_sum", "votes_total_sum",
                  "user_vote",)


class IssuePostSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    label = serializers.CharField(required=True)


class ThumbSerializer(serializers.Serializer):
    issue_iid = serializers.IntegerField(required=True)
    vote = serializers.IntegerField(required=True)

