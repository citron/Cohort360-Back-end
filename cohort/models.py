import re
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, Group as BaseGroup, \
    Permission, GroupManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zxcvbn import zxcvbn

from cohort.exceptions import UnsupportedFeatureError
from cohort_back.settings import COHORT_CONF


def is_valid_username(username, auth_type):
    username_regex = COHORT_CONF["AUTH_METHODS"][auth_type]["USERNAME_REGEX"]
    if username_regex is not None:
        pattern = re.compile(username_regex)
        if not pattern.match(username):
            return False
    return True


class UserManager(BaseUserManager):
    def create_simple_user(self, username, auth_type, password, email=None):
        if not username:
            raise ValueError('Users must have an username.')
        if not auth_type:
            raise ValueError('Users must have a type (SIMPLE|LDAP).')

        if auth_type == 'SIMPLE':
            if not email:
                raise ValueError('Users with auth_type=SIMPLE must specify a valid email address.')

            if zxcvbn(password, [])['score'] < 2:
                raise ValueError("Password is too weak.")
            elif zxcvbn(password, [])['score'] > 4:
                raise ValueError("Password is too complex.")

        if not is_valid_username(username=username, auth_type=auth_type):
            raise ValueError("Invalid username.")

        if auth_type == 'LDAP':
            if email:
                raise ValueError('Users with auth_type=LDAP cannot specify an email address.')

            # TODO: check that the user exists in LDAP and get its email address for later
            exists_in_ldap = True
            if not exists_in_ldap:
                raise ValueError("User does not exists in LDAP.")

        user = get_user_model()(username=username, auth_type=auth_type, email=email)
        if auth_type == 'SIMPLE':
            user.set_password(password)
        if auth_type == 'LDAP':
            # Verify the password via ldap
            # TODO
            user.is_active = True
        user.save(using=self.db)
        return user

    def create_super_user(self, username, password, email):
        user = self.create_simple_user(username=username, auth_type="SIMPLE", password=password, email=email)
        user.is_superuser = True
        user.is_active = True
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
    REQUIRED_FIELDS = ['auth_type']

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField('email address', max_length=254, unique=True, null=True)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    AUTH_TYPE_CHOICES = [("SIMPLE", 'Simple'), ('LDAP', 'LDAP')]
    auth_type = models.CharField(max_length=6, choices=AUTH_TYPE_CHOICES)

    def set_password(self, raw_password):
        if self.auth_type == 'SIMPLE':
            super(User, self).set_password(raw_password)
        if self.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def check_password(self, raw_password):
        if self.auth_type == 'SIMPLE':
            return super(User, self).check_password(raw_password)
        if self.auth_type == 'LDAP':
            # TODO
            return True

    def get_groups(self):
        return Group.objects.filter(members__in=[self])

    def is_admin(self):
        if self.is_superuser:
            return True
        return self in Group.objects.get(name="admin").members


class Group(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField('name', max_length=80, unique=True)
    members = models.ManyToManyField(User)
    objects = GroupManager()

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def add_member(self, user):
        if user.auth_type == 'SIMPLE':
            self.members.add(user)
            self.save()
        if user.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def del_member(self, user):
        if user.auth_type == 'SIMPLE':
            self.members.remove(user)
            self.save()
        if user.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def is_member(self, user):
        try:
            self.members.get(user=user)
            return True
        except ObjectDoesNotExist:
            return False

    def refresh_from_ldap(self):
        # TODO
        mappings = COHORT_CONF["AUTH_METHODS"]["LDAP"]["GROUPS_MAPPING"]
        pass
