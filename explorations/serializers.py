from rest_framework import serializers

from cohort.models import User
from cohort.serializers import BaseSerializer, UserSerializer
from explorations.models import Request, CohortResult, RequestQuerySnapshot, DatedMeasure


class PrimaryKeyRelatedFieldWithOwner(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context.get("request", None).user
        if user is None:
            raise Exception("Internal error: No context request provided to serializer")
        qs = super(PrimaryKeyRelatedFieldWithOwner, self).get_queryset()
        if user.is_superuser:
            return qs
        return qs.filter(owner=user)


class UserPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context.get("request", None).user
        if user is None:
            raise Exception("Internal error: No context request provided to serializer")
        qs = super(UserPrimaryKeyRelatedField, self).get_queryset()
        if user.is_superuser:
            return qs
        return qs.filter(uuid=user.uuid)


class RequestSerializer(BaseSerializer):
    owner_id = UserPrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)

    class Meta:
        model = Request
        exclude = ["owner"]

    def update(self, instance, validated_data):
        for f in ['owner']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(RequestSerializer, self).update(instance, validated_data)

    def partial_update(self, instance, validated_data):
        for f in ['owner']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(RequestSerializer, self).partial_update(instance, validated_data)


class RequestQuerySnapshotSerializer(BaseSerializer):
    request_id = PrimaryKeyRelatedFieldWithOwner(source='request', queryset=Request.objects.all(), required=False)
    owner_id = UserPrimaryKeyRelatedField(source='owner', queryset=User.objects.all(), required=False)
    previous_snapshot_id = PrimaryKeyRelatedFieldWithOwner(
        source='previous_snapshot', queryset=RequestQuerySnapshot.objects.all(), required=False
    )

    class Meta:
        model = RequestQuerySnapshot
        exclude = ["request", "owner"]
        read_only_fields = ["is_active_branch"]

    def create(self, validated_data):
        previous_snapshot = validated_data.get("previous_snapshot", None)
        request = validated_data.get("request", None)
        if previous_snapshot is not None:
            for rqs in previous_snapshot.next_snapshots.all():
                rqs.active = False
                rqs.save()
            if request is not None and request.uuid != previous_snapshot.request.uuid:
                raise serializers.ValidationError(
                    "You cannot provide a request_id that is not the same as the id "
                    "of the request binded to the previous_snapshot")
            validated_data["request"] = previous_snapshot.request
        elif request is not None:
            if len(request.query_snapshots.all()) != 0:
                raise serializers.ValidationError("You have to provide a previous_snapshot_id if the request is not"
                                                  " empty of query snaphots")
        else:
            raise serializers.ValidationError(
                "You have to provide a previous_snapshot_id or a request_id if the request "
                "has not query snapshots binded to it yet")

        return super(RequestQuerySnapshotSerializer, self).create(validated_data=validated_data)

    def update(self, instance, validated_data):
        for f in ['owner', 'request']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(RequestQuerySnapshotSerializer, self).update(instance, validated_data)

    def partial_update(self, instance, validated_data):
        for f in ['owner', 'request']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(RequestQuerySnapshotSerializer, self).partial_update(instance, validated_data)


class DatedMeasureSerializer(BaseSerializer):
    request_query_snapshot_id = PrimaryKeyRelatedFieldWithOwner(source='request_query_snapshot',
                                                                queryset=RequestQuerySnapshot.objects.all())
    request_id = PrimaryKeyRelatedFieldWithOwner(source='request', queryset=Request.objects.all(), required=False)
    owner_id = UserPrimaryKeyRelatedField(source='owner', queryset=User.objects.all())

    class Meta:
        model = DatedMeasure
        exclude = ["request_query_snapshot", "request", "owner"]

    def update(self, instance, validated_data):
        for f in ['owner', 'request', 'request_query_snapshot']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(DatedMeasureSerializer, self).update(instance, validated_data)

    def partial_update(self, instance, validated_data):
        for f in ['owner', 'request', 'request_query_snapshot']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot bu updated manually')
        return super(DatedMeasureSerializer, self).partial_update(instance, validated_data)

    def create(self, validated_data):
        rqs = validated_data.get("request_query_snapshot", None)
        req = validated_data.get("request", None)
        if rqs is not None:
            if req is not None:
                if req.uuid != rqs.request.uuid:
                    raise serializers.ValidationError(
                        "YOu cannot provide different from the one the query_snapshot is binded to")
            else:
                validated_data["request"] = rqs.request
        else:
            raise serializers.ValidationError("You have to provide a request_query_snapshot_id to bind the dated"
                                              " measure to it")

        return super(DatedMeasureSerializer, self).create(validated_data=validated_data)


class CohortResultSerializer(BaseSerializer):
    dated_measure_id = PrimaryKeyRelatedFieldWithOwner(queryset=DatedMeasure.objects.all(),
                                                       required=False, allow_null=True)
    dated_measure = DatedMeasureSerializer(required=False, allow_null=True)
    request_query_snapshot_id = PrimaryKeyRelatedFieldWithOwner(source='request_query_snapshot',
                                                                queryset=RequestQuerySnapshot.objects.all())
    request_id = PrimaryKeyRelatedFieldWithOwner(source='request', queryset=Request.objects.all(), required=False)
    owner_id = UserPrimaryKeyRelatedField(source='owner', queryset=User.objects.all())
    owner = UserSerializer(required=False, read_only=True)
    result_size = serializers.IntegerField(read_only=True)

    fhir_group_id = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = CohortResult
        exclude = ["request_query_snapshot", "request"]

    def update(self, instance, validated_data):
        for f in ['owner', 'request', 'request_query_snapshot', 'dated_measure', 'dated_measure_id', 'type']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot be updated manually')
        return super(CohortResultSerializer, self).update(instance, validated_data)

    def partial_update(self, instance, validated_data):
        for f in ['owner', 'request', 'request_query_snapshot', 'dated_measure', 'type']:
            if f in validated_data:
                raise serializers.ValidationError(f'{f} field cannot be updated manually')
        return super(CohortResultSerializer, self).partial_update(instance, validated_data)

    def create(self, validated_data):
        rqs = validated_data.get("request_query_snapshot", None)
        req = validated_data.get("request", None)
        if rqs is not None:
            if req is not None:
                if req.uuid != rqs.request.uuid:
                    raise serializers.ValidationError(
                        "YOu cannot provide different from the one the query_snapshot is binded to")
            else:
                validated_data["request"] = rqs.request
        else:
            raise serializers.ValidationError("You have to provide a request_query_snapshot_id to bind the cohort"
                                              " result to it")

        dm = validated_data.pop("dated_measure_id", None)
        if dm is None:
            dm = validated_data.pop("dated_measure", None)
            if dm is not None:
                dm_serializer = DatedMeasureSerializer(
                    data={
                        **dm,
                        "owner_id": dm["owner"].uuid, "request_query_snapshot_id": dm["request_query_snapshot"].uuid
                    }, context=self.context)
                dm_serializer.is_valid(raise_exception=True)
                dm = dm_serializer.save()
                validated_data["dated_measure"] = dm
            else:
                raise serializers.ValidationError(
                    "You have to provide either dated_measure_id or a dated_measure object")
        else:
            # serializer will have retrieved the dated_measure matching the id
            validated_data["dated_measure_id"] = dm.uuid

        return super(CohortResultSerializer, self).create(validated_data=validated_data)

