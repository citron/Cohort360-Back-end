from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user:
            return False
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin()


class IsShared(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "shared"):
            return obj.shared
        return False
