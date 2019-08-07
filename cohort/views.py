from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from cohort.models import User
from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.serializers import UserSerializer


class BaseViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)


class UserObjectsRestrictedViewSet(BaseViewSet):
    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.__class__.queryset
        if self.__class__ == UserViewSet:
            return self.__class__.queryset.filter(uuid=self.request.user.uuid)
        return self.__class__.queryset.filter(owner=self.request.user)


class UserViewSet(UserObjectsRestrictedViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'delete']

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
