from rest_framework import serializers
from rest_framework.fields import Field, _UnvalidatedField

from cohort.serializers import BaseSerializer
from voting.models import GitlabIssue


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

    class Meta:
        model = GitlabIssue
        fields = ("iid", "state", 'labels',
                  "gitlab_created_at", "gitlab_updated_at", "gitlab_closed_at",
                  "title", "description",
                  "votes_positive_sum", "votes_neutral_sum", "votes_negative_sum", "votes_total_sum",)
