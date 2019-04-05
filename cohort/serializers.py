from django.db import IntegrityError
from rest_framework import serializers
from django.contrib.auth import get_user_model

from cohort.models import UserManager, is_valid_username, Group

UserModel = get_user_model()


class UserSerializerCreate(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(max_length=254, required=False)
    auth_type = serializers.ChoiceField(choices=UserModel.AUTH_TYPE_CHOICES)
    is_active = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        user = None
        try:
            user = UserManager().create_simple_user(**validated_data)
        except ValueError as ve:
            raise serializers.ValidationError(str(ve), code="value_error")
        except IntegrityError as e:
            if 'username' in str(e):
                raise serializers.ValidationError("User already exists!", code="user_already_exists")
            if 'email' in str(e):
                raise serializers.ValidationError("Email already associated to an existing user!",
                                                  code="user_already_exists")
        except Exception as e:
            raise serializers.ValidationError(str(e), code="internal")
        return user

    class Meta:
        model = UserModel
        fields = ("uuid", "created_at", "modified_at",
                  "username", "password", "email", "auth_type", "is_active")


class UserSerializerUpdate(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(max_length=254, required=False)
    auth_type = serializers.ChoiceField(choices=UserModel.AUTH_TYPE_CHOICES, read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    def update(self, instance, validated_data):
        if 'username' in validated_data:
            if self.auth_type != "SIMPLE":
                raise ValueError("Username can only be changed for SIMPLE auth users!")

            if not is_valid_username(username=validated_data['username'], auth_type=instance.auth_type):
                raise ValueError("Invalid username.")
            instance.username = validated_data['username']

        if 'email' in validated_data:
            if instance.auth_type != "SIMPLE":
                raise ValueError("Email can only be changed for SIMPLE auth users!")

            instance.email = validated_data.get('email', instance.email)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()
        return instance

    class Meta:
        model = UserModel
        fields = ("uuid", "created_at", "modified_at",
                  "username", "password", "email", "auth_type", "is_active")


class GroupSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    name = serializers.CharField(max_length=80)
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=UserModel.objects.all(), required=False)
    ldap_corresponding_group = serializers.CharField(max_length=500, required=False)

    class Meta:
        model = Group
        fields = ("uuid", "created_at", "modified_at",
                  "name", "members", "ldap_corresponding_group")

