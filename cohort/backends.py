from cohort.auth import IDServer
from cohort.models import get_or_create_user, User
from cohort_back.settings import JWT_SERVER_ACCESS_KEY, JWT_SERVER_REFRESH_KEY


class AuthBackend:
    def authenticate(self, request, username, password):
        try:
            tokens = IDServer.check_ids(username=username, password=password)
        except ValueError:
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = get_or_create_user(jwt_access_token=tokens['access'])

        request.jwt_session_key = tokens[JWT_SERVER_ACCESS_KEY]
        request.jwt_refresh_key = tokens[JWT_SERVER_REFRESH_KEY]
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
