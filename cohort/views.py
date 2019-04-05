from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from cohort.models import User, Group
from cohort.permissions import IsOwner, IsAdmin
from cohort.serializers import UserSerializerCreate, UserSerializerUpdate, GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializerCreate
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('username', 'email', 'is_active',)
    ordering_fields = ('created_at', 'modified_at', 'username', 'email',)
    ordering = ('username',)
    search_fields = ('$username', '$email',)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            serializer_class = UserSerializerUpdate

        return serializer_class

    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdmin(), IsOwner()]
        elif self.request.method == 'POST':
            return [AllowAny()]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name',)
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)
    search_fields = ('$name',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
            return [IsAdmin()]
