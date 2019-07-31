from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets
from rest_framework.response import Response

from cohort.models import User
from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.serializers import UserSerializerCreate


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
    http_method_names = ['get', 'post', 'patch', 'delete']

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
        #
        # if self.request and self.request.method == 'PATCH':
        #     serializer_class = UserSerializerUpdate

        return serializer_class

    def get_permissions(self):
        if self.request.method in ['GET']:
            return OR(IsAdminOrOwner())
        elif self.request.method in ['DELETE']:
            return OR(IsAdmin())
        return []
