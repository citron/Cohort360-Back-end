from django.http import HttpResponseForbidden, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.deprecation import MiddlewareMixin
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPE_BYTES
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from cohort.auth import IDServer
from cohort.models import User, get_or_create_user
from cohort.tasks import import_i2b2_if_needed_else_background


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):

        if 'Authorization' in request.META:
            jwt_access_token = request.META['Authorization']

            try:
                payload = IDServer.verify_jwt(jwt_access_token)
            except ValueError:
                return HttpResponseUnauthorized('<h1>401 Invalid or expired JWT token</h1>', content_type='text/html')
            try:
                request.user = User.objects.get(username=payload['username'])
            except User.DoesNotExist:
                request.user = get_or_create_user(jwt_access_token=jwt_access_token)
                import_i2b2_if_needed_else_background(request.user, jwt_access_token=jwt_access_token)
            return
        return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            payload = IDServer.verify_jwt(raw_token)
        except ValueError:
            return HttpResponseUnauthorized('<h1>401 Invalid or expired JWT token</h1>', content_type='text/html')
        try:
            u = User.objects.get(username=payload['username'])
            return u, raw_token
        except User.DoesNotExist:
            user = get_or_create_user(jwt_access_token=raw_token)
            import_i2b2_if_needed_else_background(user, jwt_access_token=raw_token)
            return user, raw_token

    def get_header(self, request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        header = request.META.get('HTTP_AUTHORIZATION')

        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)

        return header

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed(
                _('Authorization header must contain two space-delimited values'),
                code='bad_authorization_header',
            )

        return parts[1]
