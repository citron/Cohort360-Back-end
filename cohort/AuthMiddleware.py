import jwt
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from cohort.auth import IDServer
from cohort.models import User, get_or_create_user


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):

        if 'Authorization' in request.META:
            jwt_access_token = request.META['Authorization']

            if IDServer.verify_jwt(jwt_access_token):
                username = jwt.decode(jwt_access_token, 'secret', algorithms=['HS256'])['username']
                try:
                    request.user = User.objects.get(username=username)
                except User.DoesNotExist:
                    request.user = get_or_create_user(jwt_access_token=jwt_access_token)
                return
        # return HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')
