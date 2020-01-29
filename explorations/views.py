import coreapi
import coreschema
from rest_framework.decorators import permission_classes, action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.views import APIView

from cohort.models import Perimeter
from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.views import UserObjectsRestrictedViewSet
from explorations.models import Exploration, Request, Cohort, RequestQuerySnapshot, RequestQueryResult
from explorations.serializers import ExplorationSerializer, RequestSerializer, CohortSerializer, \
    RequestQuerySnapshotSerializer, RequestQueryResultSerializer, PerimeterSerializer


# Filtering/Ordering/Searching : https://www.django-rest-framework.org/api-guide/filtering/
#
# filterset_fields = ('category', 'in_stock',) -> /api/products?category=clothing&in_stock=True
# ordering_fields = ('username',) -> /api/users?ordering=username
# ordering = ('name',) -> This is the default ordering
# search_fields = ('user',) -> /api/users?search=russell


class CohortViewSet(UserObjectsRestrictedViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
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

        return super(CohortViewSet, self).create(request, *args, **kwargs)


class RequestQueryResultViewSet(UserObjectsRestrictedViewSet):
    queryset = RequestQueryResult.objects.all()
    serializer_class = RequestQueryResultSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid',
                        'request_query_snapshot_id', 'request_id', 'perimeter_id',
                        'refresh_every_seconds', 'refresh_create_cohort')
    ordering_fields = ('created_at', 'modified_at',
                       'result_size', 'refresh_every_seconds')
    ordering = ('-created_at',)
    search_fields = []

    def create(self, request, *args, **kwargs):
        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)

        return super(RequestQueryResultViewSet, self).create(request, *args, **kwargs)


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

    @action(detail=True, methods=['get'])
    @permission_classes((IsAdminOrOwner,))
    def generate_result(self, request_query_snapshot_uuid, perimeter_uuid):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
            p = Perimeter.objects.get(uuid=perimeter_uuid)
        except (RequestQuerySnapshot.DoesNotExist, Perimeter.DoesNotExist):
            return Response({"response": "request_query_snapshot or perimeter not found"},
                            status=status.HTTP_404_NOT_FOUND)
        rqr = rqs.generate_result(perimeter=p)
        return Response({'response': "Query successful!", 'data': RequestQueryResultSerializer(rqr).data},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    @permission_classes((IsAdminOrOwner,))
    def generate_cohort(self, request_query_snapshot_uuid, perimeter_uuid, name, description):
        try:
            rqs = RequestQuerySnapshot.objects.get(uuid=request_query_snapshot_uuid)
            p = Perimeter.objects.get(uuid=perimeter_uuid)
        except (RequestQuerySnapshot.DoesNotExist, Perimeter.DoesNotExist):
            return Response({"response": "request_query_snapshot or perimeter not found"},
                            status=status.HTTP_404_NOT_FOUND)
        c = rqs.generate_cohort(name, description, perimeter=p)
        return Response({'response': "Query successful!", 'data': CohortSerializer(c).data},
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


class ExplorationViewSet(UserObjectsRestrictedViewSet):
    queryset = Exploration.objects.all()
    serializer_class = ExplorationSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid', 'name', 'favorite', 'owner_id',)
    ordering_fields = ('created_at', 'modified_at',
                       'name', 'description', 'favorite', 'owner_id',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):

        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)

        return super(ExplorationViewSet, self).create(request, *args, **kwargs)


class PerimeterViewSet(UserObjectsRestrictedViewSet):
    queryset = Perimeter.objects.all()
    serializer_class = PerimeterSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filterset_fields = ('uuid', 'name', 'data_type', 'owner_id',)
    ordering_fields = ('created_at', 'modified_at',
                       'name', 'description', 'data_type', 'owner_id',)
    ordering = ('name',)
    search_fields = ('$name', '$description', '$fhir_query')

    def get_permissions(self):
        if self.request.method in ['POST', 'PATCH', 'DELETE']:
            return OR(IsAdmin())
        elif self.request.method == 'GET':
            return OR(IsAdminOrOwner())

    def create(self, request, *args, **kwargs):

        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)

        return super(PerimeterViewSet, self).create(request, *args, **kwargs)


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
