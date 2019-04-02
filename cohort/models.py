from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin, Group as BaseGroup, \
    Permission, GroupManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from cohort.exceptions import UnsupportedFeatureError


class UserManager(BaseUserManager):
    def create_simple_user(self, username, auth_type, password, email=None):
        if not username:
            raise ValueError('Users must have an username.')
        if not auth_type:
            raise ValueError('Users must have a type (SIMPLE|LDAP).')

        if auth_type == 'LDAP':
            # TODO: check that the user exists in LDAP and get its email address for later
            exists_in_ldap = True
            if not exists_in_ldap:
                raise ValueError("User does not exists in LDAP.")

        user = get_user_model()(username=username, type=auth_type, email=email)
        if auth_type == 'SIMPLE':
            user.set_password(password)
        user.is_active = True
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password=password)
        user.is_staff = True
        user.is_active = True
        user.save(using=self.db)
        return user


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
            super(User).set_password(raw_password)
        if self.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def check_password(self, raw_password):
        if self.auth_type == 'SIMPLE':
            super(User).check_password(raw_password)
        if self.auth_type == 'LDAP':
            # TODO
            return True

    def get_groups(self):
        return Group.objects.filter(members__in=[self])

    def get_user_permissions(self, *args, **kwargs):
        return set()

    def get_group_permissions(self, obj=None):
        if not self.is_active:
            return set()

        if self.is_superuser:
            return Permission.objects.all()

        my_groups = self.get_groups()
        return Permission.objects.filter(groups__in=my_groups)

    def get_all_permissions(self, obj=None):
        return self.get_group_permissions()

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        return perm in self.get_all_permissions(obj)


    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        return any(
            perm[:perm.index('.')] == app_label
            for perm in self.get_all_permissions(self)
        )



class Group(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField('name', max_length=80, unique=True)
    members = models.ManyToManyField(User)
    auth_type = models.CharField(max_length=6, choices=[("SIMPLE", 'Simple'), ('LDAP', 'LDAP')])
    permissions = models.ManyToManyField(
        Permission,
        verbose_name='permissions',
        blank=True,
        related_name='groups'
    )

    objects = GroupManager()

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def add_member(self, user):
        if self.auth_type == 'SIMPLE':
            self.members.add(user)
            self.save()
        if self.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def del_member(self, user):
        if self.auth_type == 'SIMPLE':
            self.members.remove(user)
            self.save()
        if self.auth_type == 'LDAP':
            raise UnsupportedFeatureError()

    def is_member(self, user):
        if self.auth_type == 'SIMPLE':
            try:
                self.members.get(user=user)
                return True
            except ObjectDoesNotExist:
                return False
        if self.auth_type == 'LDAP':
            # TODO
            return True

    def refresh_from_ldap(self):
        # TODO
        pass
