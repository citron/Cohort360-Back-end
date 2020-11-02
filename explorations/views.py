import coreapi
import coreschema
from rest_framework.decorators import permission_classes, action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView

from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.views import UserObjectsRestrictedViewSet
from explorations.models import Request, CohortResult, RequestQuerySnapshot, DatedMeasure
from explorations.serializers import RequestSerializer, CohortResultSerializer, \
    RequestQuerySnapshotSerializer, DatedMeasureSerializer


# Filtering/Ordering/Searching : https://www.django-rest-framework.org/api-guide/filtering/
#
# filterset_fields = ('category', 'in_stock',) -> /api/products?category=clothing&in_stock=True
# ordering_fields = ('username',) -> /api/users?ordering=username
# ordering = ('name',) -> This is the default ordering
# search_fields = ('user',) -> /api/users?search=russell


class DatedMeasureViewSet(UserObjectsRestrictedViewSet):
    queryset = DatedMeasure.objects.all()
    serializer_class = DatedMeasureSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid',
                        'request_query_snapshot_id', 'request_id', 'perimeter_id',
                        'refresh_every_seconds', 'refresh_create_cohort')
    ordering_fields = ('created_at', 'modified_at',
                       'result_size', 'refresh_every_seconds')
    ordering = ('-created_at',)
    search_fields = []

    def get_permissions(self):
        if self.request.method in ['GET']:
            return OR(IsAdminOrOwner())
        else:
            return OR(IsAdmin())


class RequestQuerySnapshotViewSet(UserObjectsRestrictedViewSet):
    queryset = RequestQuerySnapshot.objects.all()
    serializer_class = RequestQuerySnapshotSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid', 'request_id',)
    ordering_fields = ('created_at', 'modified_at',)
    ordering = ('-created_at',)
    search_fields = ('$serialized_query',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)

        return super(RequestQuerySnapshotViewSet, self).create(request, *args, **kwargs)

    @action(detail=True, methods=['get'], permission_classes=(IsAdminOrOwner,), url_path="generate-result")
    def generate_result(self, req, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        rqr = rqs.generate_result()
        return Response({'response': "Query successful!", 'data': DatedMeasureSerializer(rqr).data},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=(IsAdminOrOwner,), url_path="generate-cohort")
    def generate_cohort(self, req, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        c = rqs.generate_cohort(req["name"], req["description"])
        return Response({'response': "Query successful!", 'data': CohortResultSerializer(c).data},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=(IsAdminOrOwner,), url_path="save")
    def save(self, req, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        rqs.save_snapshot()
        return Response({'response': "Query successful!"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=(IsAdminOrOwner,), url_path="get-previous")
    def get_previous(self, req, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        prvs = rqs.previous_snapshot
        if prvs is None:
            return Response({'response': "request_query_snapshot has no previous snapshot"},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'response': "Query successful!", 'data': prvs},
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=(IsAdminOrOwner,), url_path="get-next")
    def get_next(self, request_query_snapshot_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
        except RequestQuerySnapshot.DoesNotExist:
            return Response({"response": "request_query_snapshot not found"},
                            status=status.HTTP_404_NOT_FOUND)
        nxt = rqs.active_next_snapshot
        if nxt is None:
            return Response({'response': "request_query_snapshot has no active next snapshot"},
                            status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'response': "Query successful!", 'data': nxt},
                            status=status.HTTP_200_OK)


class RequestViewSet(UserObjectsRestrictedViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid', 'name', 'favorite',
                        'exploration_id', 'data_type_of_query',)
    ordering_fields = ('created_at', 'modified_at',
                       'name', 'favorite', 'data_type_of_query')
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user
        if 'owner_id' not in request.data:
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


class CohortResultViewSet(UserObjectsRestrictedViewSet):
    queryset = CohortResult.objects.all()
    serializer_class = CohortResultSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid', 'name', 'favorite',
                        'request_query_snapshot_id',
                        'request_id', 'perimeter_id', 'fhir_groups_ids', 'type')
    ordering_fields = ('created_at', 'modified_at',
                       'name', 'favorite', 'type', 'result_size')
    ordering = ('-created_at',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):
        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)
        return super(CohortResultViewSet, self).create(request, *args, **kwargs)


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
