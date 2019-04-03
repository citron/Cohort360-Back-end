from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from cohort.models import User, Group
from cohort.permissions import IsOwner, IsAdmin
from cohort.serializers import UserSerializerCreate, UserSerializerUpdate, GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializerCreate
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            serializer_class = UserSerializerUpdate

        return serializer_class

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsOwner(), IsAdmin()]
        elif self.request.method == 'PUT' or self.request.method == 'PATCH':
            return [IsOwner(), IsAdmin()]
        elif self.request.method == 'GET':
            return [IsOwner(), IsAdmin()]
        else:
            return [AllowAny()]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get', 'patch']

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAdmin()]
        elif self.request.method == 'GET':
            return [IsAdmin()]
