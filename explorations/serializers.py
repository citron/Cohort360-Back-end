import json

from rest_framework import serializers

from cohort.models import User
from cohort.serializers import BaseSerializer, UserSerializer
import cohort_back.settings as fhir_api
from cohort_back.settings import get_fhir_authorization_header, format_json_request
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
                    "of the request bound to the previous_snapshot")
            validated_data["request"] = previous_snapshot.request
        elif request is not None:
            if len(request.query_snapshots.all()) != 0:
                raise serializers.ValidationError("You have to provide a previous_snapshot_id if the request is not"
                                                  " empty of query snaphots")
        else:
            raise serializers.ValidationError(
                "You have to provide a previous_snapshot_id or a request_id if the request "
                "has not query snapshots bound to it yet")

        serialized_query = validated_data.get("serialized_query", None)
        if serialized_query is None:
            raise serializers.ValidationError("You have to provide a serialized_query")
        else:
            try:
                json.loads(serialized_query)
            except Exception as e:
                raise serializers.ValidationError(f"Serialized_query could not be recognized as json: {e}")

            # post_validate_cohort is called this way so that fhir_api can be mocked in tests
            validate_resp = fhir_api.post_validate_cohort(
                format_json_request(serialized_query),
                get_fhir_authorization_header(self.context.get("request"))
            )
            if not validate_resp.success:
                raise serializers.ValidationError(f"Serialized_query, after formatting, "
                                                  f"is not accepted by FHIR server: {validate_resp.err_msg}")

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
        read_only_fields = [
            "count_task_id",
            "request_job_id",
            "request_job_status",
            "request_job_fail_msg",
            "request_job_duration",
        ]

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
        measure = validated_data.get("measure", None)
        fhir_datetime = validated_data.get("fhir_datetime", None)
        if rqs is None:
            raise serializers.ValidationError("You have to provide a request_query_snapshot_id to bind the dated"
                                              " measure to it")
        if req is not None:
            if req.uuid != rqs.request.uuid:
                raise serializers.ValidationError(
                    "YOu cannot provide different from the one the query_snapshot is bound to")
        else:
            validated_data["request"] = rqs.request

        if (measure is not None and fhir_datetime is None) or (measure is None and fhir_datetime is not None):
            raise serializers.ValidationError("If you provide measure or fhir_datetime, you have to provide the other")

        res_dm = super(DatedMeasureSerializer, self).create(validated_data=validated_data)

        if measure is None:
            try:
                from explorations.tasks import get_count_task
                task = get_count_task.delay(
                    get_fhir_authorization_header(self.context.get("request", None)),
                    format_json_request(str(rqs.serialized_query)),
                    res_dm.uuid
                )
                res_dm.count_task_id = task.id
                res_dm.save()
            except Exception as e:
                res_dm.delete()
                raise serializers.ValidationError(
                    f"INTERNAL ERROR: Could not launch FHIR cohort count: {e}")

        return res_dm


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
        read_only_fields = [
            "create_task_id",
            "request_job_id",
            "request_job_status",
            "request_job_fail_msg",
            "request_job_duration",
        ]

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
        if validated_data.get("type", None) is not None:
            raise serializers.ValidationError("You cannot provide a type")

        rqs = validated_data.get("request_query_snapshot", None)
        req = validated_data.get("request", None)
        if rqs is None:
            raise serializers.ValidationError("You have to provide a request_query_snapshot_id to bind the cohort"
                                              " result to it")
        if req is not None:
            if req.uuid != rqs.request.uuid:
                raise serializers.ValidationError(
                    "You cannot provide a different request from the one the query_snapshot is bound to")
        else:
            validated_data["request"] = rqs.request

        dm = validated_data.pop("dated_measure_id", None)
        if dm is None:
            dm = validated_data.pop("dated_measure", None)
            dm = dict(fhir_datetime=None, measure=None) if dm is None else dm

            if "measure" in dm and dm["measure"] is None:
                dm = DatedMeasure.objects.create(
                    owner_id=rqs.owner.uuid,
                    request_id=rqs.request.uuid,
                    request_query_snapshot_id=rqs.uuid
                )
                dm.save()
            else:
                dm_serializer = DatedMeasureSerializer(
                    data={
                        **dm,
                        "owner_id": rqs.owner.uuid,
                        "request_query_snapshot_id": rqs.uuid
                    }, context=self.context)

                dm_serializer.is_valid(raise_exception=True)
                dm = dm_serializer.save()
            validated_data["dated_measure"] = dm
        else:
            # serializer will have retrieved the dated_measure matching the id
            validated_data["dated_measure_id"] = dm.uuid

        result_cr = super(CohortResultSerializer, self).create(validated_data=validated_data)

        # once it has been created, we launch Fhir API cohort creation task to complete it,
        # if fhir_group_id was not already provided
        if validated_data.get("fhir_group_id", None) is None:
            try:
                from explorations.tasks import create_cohort_task

                task = create_cohort_task.delay(
                    get_fhir_authorization_header(self.context.get("request", None)),
                    format_json_request(str(rqs.serialized_query)),
                    result_cr.uuid
                )
                result_cr.create_task_id = task.id
                result_cr.save()
                result_cr.dated_measure.count_task_id = task.id
                result_cr.dated_measure.save()

            except Exception as e:
                result_cr.delete()
                raise serializers.ValidationError(
                    f"INTERNAL ERROR: Could not launch FHIR cohort creation: {e}")

        return result_cr
