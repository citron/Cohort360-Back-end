from rest_framework import serializers

from cohort.models import User
from explorations.models import Exploration, Request, Cohort


class ExplorationSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    favorite = serializers.BooleanField(required=False)
    shared = serializers.BooleanField(required=False)

    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    requests = serializers.PrimaryKeyRelatedField(queryset=Request.objects.all(), required=False)

    class Meta:
        model = Exploration
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "favorite", "shared", "owner",
                  "requests",)


class RequestSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    shared = serializers.BooleanField(required=False)

    stats_number_of_patients = serializers.IntegerField(read_only=True)
    stats_number_of_documents = serializers.IntegerField(read_only=True)

    refresh_every = serializers.IntegerField()
    refresh_new_number_of_patients = serializers.IntegerField(read_only=True)

    exploration = serializers.PrimaryKeyRelatedField(queryset=Exploration.objects.all())

    cohorts = serializers.PrimaryKeyRelatedField(queryset=Cohort.objects.all(), required=False)

    class Meta:
        model = Exploration
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "shared",
                  "stats_number_of_patients", "stats_number_of_documents",
                  "refresh_every", "refresh_new_number_of_patients",
                  "exploration", "cohorts",)


class CohortSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    shared = serializers.BooleanField(required=False)

    request = serializers.PrimaryKeyRelatedField(queryset=Request.objects.all())

    class Meta:
        model = Exploration
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "shared",
                  "request",)