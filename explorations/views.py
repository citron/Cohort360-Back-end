import re
from collections import OrderedDict

import coreapi
import coreschema
import django_filters
from rest_framework.filters import OrderingFilter as RestOrderingFilter
from django.http import QueryDict
from django.utils.itercompat import is_iterable
from django_filters import BaseCSVFilter, ChoiceFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_extensions.mixins import NestedViewSetMixin

from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.views import UserObjectsRestrictedViewSet
from cohort_back.views import NoDeleteViewSetMixin, NoUpdateViewSetMixin
from explorations.models import Request, CohortResult, RequestQuerySnapshot, DatedMeasure
from explorations.serializers import RequestSerializer, CohortResultSerializer, \
    RequestQuerySnapshotSerializer, DatedMeasureSerializer


class CohortFilter(django_filters.FilterSet):
    def perimeter_filter(self, queryset, field, value):
        return queryset.filter(request_query_snapshot__perimeters_ids__contains=[value])

    def perimeters_filter(self, queryset, field, value):
        return queryset.filter(request_query_snapshot__perimeters_ids__contains=value.split(","))

    name = django_filters.CharFilter(field_name='name', lookup_expr="contains")
    perimeter_id = django_filters.CharFilter(method="perimeter_filter")
    perimeters_ids = django_filters.CharFilter(method="perimeters_filter")
    min_result_size = django_filters.NumberFilter(field_name='dated_measure__measure', lookup_expr='gte')
    max_result_size = django_filters.NumberFilter(field_name='dated_measure__measure', lookup_expr='lte')
    # ?min_created_at=2015-04-23
    min_fhir_datetime = django_filters.DateTimeFilter(field_name='dated_measure__fhir_datetime', lookup_expr="gte")
    max_fhir_datetime = django_filters.DateTimeFilter(field_name='dated_measure__fhir_datetime', lookup_expr="lte")
    request_job_status = django_filters.AllValuesMultipleFilter()
    type = django_filters.AllValuesMultipleFilter()

    class Meta:
        model = CohortResult
        fields = (
            "request_job_status",
            "name",
            "perimeter_id",
            "min_result_size",
            "max_result_size",
            "min_fhir_datetime",
            "max_fhir_datetime",
            "favorite",
            "type",
            "perimeters_ids",
            "fhir_group_id"
        )


class CohortResultViewSet(NestedViewSetMixin, UserObjectsRestrictedViewSet):
    queryset = CohortResult.objects.all()
    serializer_class = CohortResultSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = "uuid"

    filter_class = CohortFilter
    ordering_fields = (
        "name",
        ("result_size", "dated_measure__measure"),
        ("fhir_datetime", "dated_measure__fhir_datetime"),
        "type",
        "favorite",
        "request_job_status"
    )
    # ordering = ('-created_at',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user

        if type(request.data) == QueryDict:
            request.data._mutable = True

        if 'parent_lookup_request_query_snapshot' in kwargs:
            request.data["request_query_snapshot_id"] = kwargs['parent_lookup_request_query_snapshot']

        if 'parent_lookup_request' in kwargs:
            request.data["request_id"] = kwargs['parent_lookup_request']

        if 'owner_id' in request.data:
            if request.data['owner_id'] != str(user.uuid):
                return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['owner_id'] = str(user.uuid)

        if 'dated_measure_id' not in request.data:
            if 'dated_measure' in request.data:
                dated_measure = request.data['dated_measure']
                if not isinstance(dated_measure, dict):
                    return Response({"message": "dated_measure should be an object"}, status=status.HTTP_400_BAD_REQUEST)
                if "request_query_snapshot_id" in request.data:
                    dated_measure["request_query_snapshot_id"] = request.data["request_query_snapshot_id"]
                dated_measure["owner_id"] = str(user.uuid)

        return super(CohortResultViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return super(CohortResultViewSet, self).list(request, *args, **kwargs)


class DatedMeasureViewSet(NestedViewSetMixin, UserObjectsRestrictedViewSet):
    queryset = DatedMeasure.objects.all()
    serializer_class = DatedMeasureSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = "uuid"

    filterset_fields = ('uuid', 'request_query_snapshot_id', 'request_id')
    ordering_fields = ('created_at', 'modified_at', 'result_size')
    ordering = ('-created_at',)
    search_fields = []

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())
        else:
            return OR(IsAdmin())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if CohortResult.objects.filter(dated_measure__uuid=instance.uuid).first() is not None:
            return Response({'message': "Cannot delete a Dated measure that is binded to a cohort result"},
                            status=status.HTTP_403_FORBIDDEN)
        return super(DatedMeasureViewSet, self).destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        if type(request.data) == QueryDict:
            request.data._mutable = True

        if 'owner_id' in request.data:
            if request.data['owner_id'] != str(user.uuid):
                return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['owner_id'] = str(user.uuid)

        if 'parent_lookup_request_query_snapshot' in kwargs:
            request.data["request_query_snapshot_id"] = kwargs['parent_lookup_request_query_snapshot']
        if 'parent_lookup_request' in kwargs:
            request.data["request_id"] = kwargs['parent_lookup_request']

        return super(DatedMeasureViewSet, self).create(request, *args, **kwargs)


class RequestQuerySnapshotViewSet(NestedViewSetMixin, NoDeleteViewSetMixin,
                                  NoUpdateViewSetMixin, UserObjectsRestrictedViewSet):
    queryset = RequestQuerySnapshot.objects.all()
    serializer_class = RequestQuerySnapshotSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = "uuid"

    filterset_fields = ('uuid', 'request_id',)
    ordering_fields = ('created_at', 'modified_at',)
    ordering = ('-created_at',)
    search_fields = ('$serialized_query',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user
        if type(request.data) == QueryDict:
            request.data._mutable = True

        if 'owner_id' in request.data:
            if request.data['owner_id'] != str(user.uuid):
                return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['owner_id'] = str(user.uuid)

        if 'parent_lookup_request' in kwargs:
            request.data["request_id"] = kwargs['parent_lookup_request']
        if 'parent_lookup_previous_snapshot_id' in kwargs:
            request.data["previous_snapshot_id"] = kwargs['parent_lookup_previous_snapshot_id']

        return super(RequestQuerySnapshotViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super(RequestQuerySnapshotViewSet, self).list(request, *args, **kwargs)

    # @action(detail=True, methods=['get'], permission_classes=(IsAdminOrOwner,), url_path="generate-result")
    # def generate_result(self, req, request_query_snapshot_uuid):
    #     try:
    #         rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
    #     except RequestQuerySnapshot.DoesNotExist:
    #         return Response({"response": "request_query_snapshot not found"},
    #                         status=status.HTTP_404_NOT_FOUND)
    #     rqr = rqs.generate_result()
    #     return Response({'response': "Query successful!", 'data': DatedMeasureSerializer(rqr).data},
    #                     status=status.HTTP_200_OK)

    # @action(detail=True, methods=['post'], permission_classes=(IsAdminOrOwner,), url_path="generate-cohort")
    # def generate_cohort(self, req, request_query_snapshot_uuid):
    #     try:
    #         rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
    #     except RequestQuerySnapshot.DoesNotExist:
    #         return Response({"response": "request_query_snapshot not found"},
    #                         status=status.HTTP_404_NOT_FOUND)
    #     c = rqs.generate_cohort(req["name"], req["description"])
    #     return Response({'response': "Query successful!", 'data': CohortResultSerializer(c).data},
    #                     status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=(IsAdminOrOwner,), url_path="save")
    def save(self, req, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        rqs.save_snapshot()
        return Response({'response': "Query successful!"}, status=status.HTTP_200_OK)


class RequestViewSet(NestedViewSetMixin, UserObjectsRestrictedViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = "uuid"

    filterset_fields = ('uuid', 'name', 'favorite', 'data_type_of_query',)
    ordering_fields = ('created_at', 'modified_at',
                       'name', 'favorite', 'data_type_of_query')
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user
        if type(request.data) == QueryDict:
            request.data._mutable = True

        if 'owner_id' in request.data:
            if request.data['owner_id'] != str(user.uuid):
                return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            request.data['owner_id'] = str(user.uuid)

        return super(RequestViewSet, self).create(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=(IsAdminOrOwner,), url_path="get-status")
    def get_status(self, req, cohort_result_uuid):
        try:
            cr = CohortResult.objects.get(uuid=cohort_result_uuid)
        except CohortResult.DoesNotExist:
            return Response({"response": "CohortResult not found"},
                            status=status.HTTP_404_NOT_FOUND)
        r = cr.check_request_status()
        return Response({'response': "Query successful!", 'data': r},
                        status=status.HTTP_200_OK)


class SearchCriteria(APIView):
    """
    Search criteria based on specified terms.
    """
    permission_classes = (IsAuthenticated,)

    schema = AutoSchema(manual_fields=[
        coreapi.Field(
            "query",
            required=True,
            location="query",
            schema=coreschema.String()
        ),
    ])

    def post(self, request):
        """
        Return a list of all users.
        """
        if "terms" not in request.data:
            return Response({"query": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        # TODO
        # Execute query(terms) in SolR

        result = {}
        return Response(result)
