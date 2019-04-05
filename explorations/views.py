from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets

from cohort.permissions import IsOwner, IsAdmin, IsShared
from explorations.models import Exploration, Request, Cohort
from explorations.serializers import ExplorationSerializer, RequestSerializer, CohortSerializer


class ExplorationViewSet(viewsets.ModelViewSet):
    queryset = Exploration.objects.all()
    serializer_class = ExplorationSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'favorite', 'shared', 'owner',)
    ordering_fields = ('created_at', 'modified_at', 'name', 'description', 'favorite', 'shared', 'owner',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdmin(), IsOwner()]
        elif self.request.method == 'GET':
            return [IsAdmin(), IsOwner(), IsShared()]


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'shared', 'stats_number_of_patients', 'stats_number_of_documents', 'refresh_every',
                        'refresh_new_number_of_patients', 'exploration',)
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdmin(), IsOwner()]
        elif self.request.method == 'GET':
            return [IsAdmin(), IsOwner(), IsShared()]


class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name', 'shared', 'request',)
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)
    search_fields = ('$name', '$description',)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdmin(), IsOwner()]
        elif self.request.method == 'GET':
            return [IsAdmin(), IsOwner(), IsShared()]
