from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission
from django.db import models

from cohort.auth import IDServer


def get_or_create_user(jwt_access_token):
    user_info = IDServer.user_info(jwt_access_token=jwt_access_token)
    user = UserManager().create_simple_user(
        username=user_info['username'],
        email=user_info['email'],
        displayname=user_info['displayname'][:50],
        firstname=user_info['firstname'][:30],
        lastname=user_info['lastname'][:30],
    )
    return user


class UserManager(BaseUserManager):
    def create_simple_user(self, username, email, displayname, firstname, lastname):
        user = get_user_model()(
            username=username,
            email=email,
            displayname=displayname,
            firstname=firstname,
            lastname=lastname,
        )
        user.is_active = True
        user.save(using=self.db)
        return user

    def create_super_user(self, *args, **kwargs):
        user = self.create_simple_user(*args, **kwargs)
        user.is_superuser = True
        user.save()


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False, auto_created=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(BaseModel, AbstractBaseUser):
    objects = UserManager()

    USERNAME_FIELD = 'username'

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField('email address', max_length=254, unique=True, null=True)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    displayname = models.CharField(max_length=50, blank=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)

    def is_admin(self):
        return self.is_superuser


class Access(models.Model):
    user = models.ForeignKey(User, related_name="accesses", on_delete=models.CASCADE)
    care_site = models.ForeignKey()

