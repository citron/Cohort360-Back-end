from rest_framework import serializers

from cohort.models import User, Group
from cohort_back.settings import COHORT_CONF
from explorations.models import Exploration, Request, Cohort


class CohortSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    shared = serializers.BooleanField(required=False)

    group_id = serializers.PrimaryKeyRelatedField(source="group", queryset=Group.objects.all())
    request_id = serializers.PrimaryKeyRelatedField(source="request", queryset=Request.objects.all())

    class Meta:
        model = Cohort
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "shared",
                  "group_id", "request_id",)


class RequestSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    shared = serializers.BooleanField(required=False)

    stats_number_of_patients = serializers.IntegerField(read_only=True)
    stats_number_of_documents = serializers.IntegerField(read_only=True)

    refresh_every = serializers.IntegerField(min_value=COHORT_CONF['REFRESH_REQUESTS']['MIN_DELAY_SEC'])
    refresh_new_number_of_patients = serializers.IntegerField(read_only=True)

    exploration_id = serializers.PrimaryKeyRelatedField(source='exploration', queryset=Exploration.objects.all())

    cohorts = CohortSerializer(many=True, read_only=True)
    cohorts_ids = serializers.PrimaryKeyRelatedField(source="cohorts", queryset=Cohort.objects.all(), write_only=True,
                                                     required=False)

    class Meta:
        model = Request
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "shared",
                  "stats_number_of_patients", "stats_number_of_documents",
                  "refresh_every", "refresh_new_number_of_patients",
                  "exploration_id",
                  "cohorts", "cohorts_ids",
                  )


class ExplorationSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    favorite = serializers.BooleanField(required=False)
    shared = serializers.BooleanField(required=False)

    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all())

    requests = RequestSerializer(many=True, read_only=True)
    requests_ids = serializers.PrimaryKeyRelatedField(source="requests", queryset=Request.objects.all(),
                                                      write_only=True, required=False)

    class Meta:
        model = Exploration
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "favorite", "shared",
                  "owner_id",
                  "requests", "requests_ids",
                  )
