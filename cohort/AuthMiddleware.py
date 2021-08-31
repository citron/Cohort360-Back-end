import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponse, \
    StreamingHttpResponse, FileResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.deprecation import MiddlewareMixin
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPE_BYTES
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from cohort.auth import IDServer
from cohort.models import User, get_or_create_user
from cohort_back.settings import JWT_SESSION_COOKIE, JWT_REFRESH_COOKIE, \
    JWT_SERVER_ACCESS_KEY, JWT_SERVER_REFRESH_KEY


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if getattr(request, "jwt_session_key", None) is not None:
            raw_token = request.jwt_session_key
        else:
            header = self.get_header(request)
            if header is None:
                return None

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

            if type(raw_token) == bytes:
                raw_token = raw_token.decode('utf-8')

        try:
            payload = IDServer.verify_jwt(raw_token)
        except ValueError:
            return None
            # return HttpResponseUnauthorized('<h1>401 Invalid or expired JWT token</h1>', content_type='text/html')

        try:
            u = User.objects.get(username=payload['username'])
            return u, raw_token
        except ObjectDoesNotExist:
            user = get_or_create_user(jwt_access_token=raw_token)
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


class CustomJwtSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_key = request.COOKIES.get(JWT_SESSION_COOKIE)
        request.jwt_session_key = session_key
        refresh_key = request.COOKIES.get(JWT_REFRESH_COOKIE)
        request.jwt_refresh_key = refresh_key

    def process_response(self, request, response):
        if request.path.startswith("/accounts/logout"):
            response.delete_cookie(
                JWT_SESSION_COOKIE
            )
            response.delete_cookie(
                JWT_REFRESH_COOKIE
            )
            return response
        session_key = request.jwt_session_key
        refresh_key = request.jwt_refresh_key

        resp_data = dict()
        if not isinstance(response, StreamingHttpResponse) \
                and not isinstance(response, FileResponse):
            try:
                resp_data = json.loads(response.content)
            except json.JSONDecodeError:
                pass

        if JWT_SESSION_COOKIE in resp_data:
            session_key = resp_data[JWT_SERVER_ACCESS_KEY]
        if JWT_REFRESH_COOKIE in resp_data:
            refresh_key = resp_data[JWT_SERVER_REFRESH_KEY]

        if session_key is not None:
            response.set_cookie(
                JWT_SESSION_COOKIE,
                session_key
            )
        if refresh_key is not None:
            response.set_cookie(
                JWT_REFRESH_COOKIE,
                refresh_key
            )
        return response
