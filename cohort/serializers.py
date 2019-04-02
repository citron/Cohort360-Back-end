from rest_framework import serializers
from django.contrib.auth import get_user_model

from cohort.models import UserManager

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(max_length=254, required=False)
    auth_type = serializers.ChoiceField(choices=UserModel.AUTH_TYPE_CHOICES)
    is_active = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        return UserManager().create_simple_user(**validated_data)

    class Meta:
        model = UserModel
        fields = ( "uuid", "created_at", "modified_at",
                   "username", "password", "email", "auth_type", "is_active")