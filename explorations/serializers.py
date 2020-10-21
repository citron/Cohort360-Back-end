from rest_framework import serializers

from cohort.models import User
from cohort.serializers import BaseSerializer
from explorations.models import Request, CohortResult, RequestQuerySnapshot, DatedMeasure


class CohortResultSerializer(BaseSerializer):
    request_query_snapshot_id = serializers.PrimaryKeyRelatedField(source='request_query_snapshot',
                                                                   queryset=RequestQuerySnapshot.objects.all())
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)
    result_size = serializers.IntegerField()

    class Meta:
        model = CohortResult
        excluded = ["owner", "request"]
        read_only_fields = ["type", "result_size"]


class DatedMeasureSerializer(BaseSerializer):
    request_query_snapshot_id = serializers.PrimaryKeyRelatedField(source='request_query_snapshot',
                                                                   queryset=RequestQuerySnapshot.objects.all())
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)

    class Meta:
        model = DatedMeasure
        excluded = ["request_query_snapshot", "request", "owner"]


class RequestQuerySnapshotSerializer(BaseSerializer):
    request_id = serializers.PrimaryKeyRelatedField(source='request', queryset=Request.objects.all())
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)
    previous_snapshot_id = serializers.PrimaryKeyRelatedField(
        source='previous_snapshot', queryset=RequestQuerySnapshot.objects.all(), required=False
    )
    next_snapshot_id = serializers.PrimaryKeyRelatedField(source='active_next_snapshot', read_only=True)

    class Meta:
        model = RequestQuerySnapshot
        fields = "__all__"
        excluded = ["request", "owner"]
        read_only_fields = ["is_active_branch"]

    def create(self, validated_data):
        previous_snapshot_id = validated_data.get("previous_snapshot_id", None)
        if previous_snapshot_id is not None:
            previous_snapshot = RequestQuerySnapshot.objects.get(uuid=previous_snapshot_id)
            for rqs in previous_snapshot.next_snapshots:
                rqs.active = False
                rqs.save()
        return super(RequestQuerySnapshotSerializer, self).create(validated_data=validated_data)


class RequestSerializer(BaseSerializer):
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)

    class Meta:
        model = Request
        excluded = ["owner"]
