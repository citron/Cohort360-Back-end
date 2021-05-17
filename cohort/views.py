import re

from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response

from cohort.models import User
from cohort.permissions import IsAdminOrOwner, OR, IsAdmin
from cohort.serializers import UserSerializer


class CustomOrderingFilter(OrderingFilter):
    # Allows to add aliases while ordering
    # for instance, you can add in a url /?ordering=alias
    # and set the viewset's ordering_fields to ("alias", "actual_field")
    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = self.get_valid_fields(queryset, view, {'request': request})
        valid_terms = [term for term in fields if term.lstrip('-') in [vf[0] for vf in valid_fields] and re.compile(r'\?|[-+]?[.\w]+$').match(term)]
        for term in valid_terms:
            ordering_term = [v_f[1] for v_f in valid_fields if v_f[0] == term.lstrip('-')][0]
            yield f"-{ordering_term}" if term[0] == '-' else ordering_term


class BaseViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend, CustomOrderingFilter, SearchFilter,)


class UserObjectsRestrictedViewSet(BaseViewSet):
    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.__class__.queryset
        if self.__class__ == UserViewSet:
            return self.__class__.queryset.filter(uuid=self.request.user.uuid)
        return self.__class__.queryset.filter(owner=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        # temp fix untill _id is not used
        if 'owner_id' in request.data:
            return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)

        return super(UserObjectsRestrictedViewSet, self).partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user = request.user
        if 'owner_id' in request.data:
            if request.data['owner_id'] != str(user.uuid):
                return Response({"message": "Cannot specify a different owner"}, status=status.HTTP_400_BAD_REQUEST)
        request.data['owner'] = str(user.uuid)
        return super(UserObjectsRestrictedViewSet, self).create(request, *args, **kwargs)

    # temp fix untill _id is not used
    def initial(self, request, *args, **kwargs):
        super(UserObjectsRestrictedViewSet, self).initial(request, *args, **kwargs)

        s = self.get_serializer_class()()
        primary_key_fields = [f.field_name for f in s._writable_fields if isinstance(f, PrimaryKeyRelatedField)]

        if isinstance(request.data, QueryDict):
            request.data._mutable = True

        for field_name in primary_key_fields:
            field_name_with_id = f'{field_name}_id'
            if field_name_with_id in request.data:
                request.data[field_name] = request.data[field_name_with_id]


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
