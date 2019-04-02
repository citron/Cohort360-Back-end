from rest_framework import viewsets

from cohort.models import User
from cohort.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer