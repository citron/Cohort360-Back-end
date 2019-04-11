from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import permission_classes, detail_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import NOT, IsAuthenticated
from rest_framework.response import Response

from cohort.models import User, Group
from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.serializers import UserSerializerCreate, UserSerializerUpdate, GroupSerializer, UserSerializer


class CustomModelViewSet(viewsets.ModelViewSet):
    def _get_list_from_queryset(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializerCreate
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('username', 'email', 'is_active', 'displayname', 'firstname', 'lastname')
    ordering_fields = ('created_at', 'modified_at', 'username', 'email', 'displayname', 'firstname', 'lastname')
    ordering = ('username', 'displayname', 'firstname', 'lastname')
    search_fields = ('$username', '$email', '$displayname', '$firstname', '$lastname')

    lookup_field = 'username'

    # def get_queryset(self):
    #     user = self.request.user
    #     # if user.is_admin():
    #     return User.objects.all()
    #     # else:
    #     #     return User.objects.filter(uuid=user.uuid)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request and (self.request.method == 'PUT' or self.request.method == 'PATCH'):
            serializer_class = UserSerializerUpdate

        return serializer_class

    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'PATCH', 'DELETE']:
            return OR(IsAdminOrOwner())
        elif self.request.method == 'POST':
            return OR(IsAdmin(), NOT(IsAuthenticated()))

    @detail_route(methods=['get'])
    @permission_classes((IsAdminOrOwner,))
    def groups(self, request, username):
        if request.user.is_admin():
            u = get_object_or_404(User, username=username)
        else:
            if username != request.user.username:
                raise PermissionDenied()
            u = request.user
        serializer = GroupSerializer(u.get_groups(), many=True)
        return Response(serializer.data)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    lookup_field = 'name'

    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('name',)
    ordering_fields = ('created_at', 'modified_at', 'name',)
    ordering = ('name',)  # by default
    search_fields = ('$name',)

    def get_permissions(self):
        if self.request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            return OR(IsAdmin())

    @detail_route(methods=['get'])
    @permission_classes((IsAdminOrOwner,))
    def members(self, request, name):
        g = get_object_or_404(Group, name=name)
        serializer = UserSerializer(g.members, many=True)
        return Response(serializer.data)
