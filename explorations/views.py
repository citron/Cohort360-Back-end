from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets

from cohort.permissions import IsOwner, IsAdmin, IsShared, OR
from cohort.views import CustomModelViewSet
from explorations.models import Exploration, Request, Cohort
from explorations.serializers import ExplorationSerializer, RequestSerializer, CohortSerializer


class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'shared', 'request_id', 'group_id')
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Cohort.objects.all()
        else:
            return Cohort.objects.filter(request__exploration__owner=user)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return OR(IsAdmin(), IsOwner())
        elif self.request.method == 'GET':
            return OR(IsAdmin(), IsOwner(), IsShared())


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'shared', 'stats_number_of_patients', 'stats_number_of_documents', 'refresh_every',
                        'refresh_new_number_of_patients', 'exploration_id',)
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Request.objects.all()
        else:
            return Request.objects.filter(exploration__owner=user)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return OR(IsAdmin(), IsOwner())
        elif self.request.method == 'GET':
            return OR(IsAdmin(), IsOwner(), IsShared())


class ExplorationViewSet(CustomModelViewSet):
    queryset = Exploration.objects.all()
    serializer_class = ExplorationSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'favorite', 'shared', 'owner_id',)
    ordering_fields = ('created_at', 'modified_at', 'name', 'description', 'favorite', 'shared', 'owner_id',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Exploration.objects.all()
        else:
            return Exploration.objects.filter(owner=user)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return OR(IsAdmin(), IsOwner())
        elif self.request.method == 'GET':
            return OR(IsAdmin(), IsOwner(), IsShared())

    def create(self, request, *args, **kwargs):

        user = request.user

        if 'owner_id' not in request.data:
            request.data['owner_id'] = str(user.uuid)

        return super(ExplorationViewSet, self).create(request, *args, **kwargs)
