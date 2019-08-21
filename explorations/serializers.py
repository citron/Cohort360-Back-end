from rest_framework import serializers

from cohort.models import User, Perimeter
from cohort.serializers import BaseSerializer
from explorations.models import Exploration, Request, Cohort, RequestQuerySnapshot, RequestQueryResult


class CohortSerializer(BaseSerializer):
    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)

    request_query_snapshot_id = serializers.PrimaryKeyRelatedField(source='request_query_snapshot',
                                                                   queryset=RequestQuerySnapshot.objects.all())
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    perimeter_id = serializers.PrimaryKeyRelatedField(source='perimeter', queryset=Perimeter.objects.all())

    fhir_group_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cohort
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", 'favorite',
                  "request_query_snapshot_id", "request_id", "perimeter_id",
                  "fhir_group_id",)


class RequestQueryResultSerializer(BaseSerializer):
    request_query_snapshot_id = serializers.PrimaryKeyRelatedField(source='request_query_snapshot',
                                                                   queryset=RequestQuerySnapshot.objects.all())
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    perimeter_id = serializers.PrimaryKeyRelatedField(source='perimeter', queryset=Perimeter.objects.all())

    result_size = serializers.IntegerField(read_only=True)

    refresh_every_seconds = serializers.IntegerField(required=False)
    refresh_create_cohort = serializers.BooleanField(required=False)

    class Meta:
        model = RequestQueryResult
        fields = ("uuid", "created_at", "modified_at",
                  "request_query_snapshot_id", "request_id", "perimeter_id",
                  "result_size",
                  "refresh_every_seconds", "refresh_create_cohort",)


class RequestQuerySnapshotSerializer(BaseSerializer):
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    serialized_query = serializers.CharField(required=False)

    class Meta:
        model = RequestQuerySnapshot
        fields = ("uuid", "created_at", "modified_at",
                  "request_id", "serialized_query",)


class RequestSerializer(BaseSerializer):
    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    favorite = serializers.BooleanField(required=False)

    exploration_id = serializers.PrimaryKeyRelatedField(source='exploration', queryset=Exploration.objects.all())

    data_type_of_query = serializers.ChoiceField(Request.REQUEST_DATA_TYPE_CHOICES)

    class Meta:
        model = Request
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "favorite",
                  "exploration_id",
                  "data_type_of_query",)


class ExplorationSerializer(BaseSerializer):
    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)
    favorite = serializers.BooleanField(required=False)

    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all())

    class Meta:
        model = Exploration
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description", "favorite",
                  "owner_id",)


class PerimeterSerializer(BaseSerializer):
    name = serializers.CharField(max_length=30)
    description = serializers.CharField(required=False)

    data_type = serializers.ChoiceField(choices=Perimeter.PERIMETER_DATA_TYPE_CHOICES)
    fhir_query = serializers.CharField()

    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all())

    class Meta:
        model = Perimeter
        fields = ("uuid", "created_at", "modified_at",
                  "name", "description",
                  "owner_id",
                  "data_type", "fhir_query",)
