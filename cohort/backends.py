from cohort.auth import IDServer
from cohort.models import get_or_create_user, User


class AuthBackend:
    def authenticate(self, request, username, password):
        try:
            tokens = IDServer.check_ids(username=username, password=password)
        except ValueError:
            return None
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            user = get_or_create_user(jwt_access_token=tokens['access'])
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
