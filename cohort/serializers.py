from rest_framework import serializers

from cohort.models import User


class BaseSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    # Extra feature (https://www.django-rest-framework.org/api-guide/serializers/#example)
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        super(BaseSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserSerializer(BaseSerializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(max_length=254, required=False)
    is_active = serializers.BooleanField(read_only=True)

    displayname = serializers.CharField(max_length=50, required=False)
    firstname = serializers.CharField(max_length=30, required=False)
    lastname = serializers.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ("uuid", "created_at", "modified_at",
                  "username", "password", "email", "is_active",
                  "displayname", "firstname", "lastname",)

#
# class UserSerializerCreate(UserSerializer):
#     class Meta(UserSerializer.Meta):
#         pass
#
#     def create(self, validated_data):
#         user = None
#         try:
#             user = UserManager().create_simple_user(**validated_data)
#         except ValueError as ve:
#             raise serializers.ValidationError(str(ve), code="value_error")
#         except IntegrityError as e:
#             if 'username' in str(e):
#                 raise serializers.ValidationError("User already exists!", code="user_already_exists")
#             if 'email' in str(e):
#                 raise serializers.ValidationError("Email already associated with an existing user!",
#                                                   code="user_already_exists")
#         except Exception as e:
#             raise serializers.ValidationError(str(e), code="internal")
#         return user


#
# class UserSerializerUpdate(UserSerializer):
#     class Meta(UserSerializer.Meta):
#         pass
#
#     def update(self, instance, validated_data):
#         if 'username' in validated_data:
#             if self.auth_type != "SIMPLE":
#                 raise ValueError("Username can only be changed for SIMPLE auth users!")
#
#             if not is_valid_username(username=validated_data['username'], auth_type=instance.auth_type):
#                 raise ValueError("Invalid username.")
#             instance.username = validated_data['username']
#
#         if 'email' in validated_data:
#             if instance.auth_type != "SIMPLE":
#                 raise ValueError("Email can only be changed for SIMPLE auth users!")
#
#             instance.email = validated_data.get('email', instance.email)
#
#         if 'password' in validated_data:
#             instance.set_password(validated_data['password'])
#
#         instance.displayname = validated_data.get('displayname', instance.displayname)
#         instance.firstname = validated_data.get('firstname', instance.firstname)
#         instance.lastname = validated_data.get('lastname', instance.lastname)
#
#         instance.save()
#         return instance
