"""cohort_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers, permissions
from rest_framework_swagger.views import get_swagger_view

from cohort.views import UserViewSet
from explorations.views import SearchCriteria
# Routers provide an easy way of automatically determining the URL conf.
from voting.views import IssuePost

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
# router.register(r'voting/issues', GitlabIssueViewSet)

old_schema_view = get_swagger_view(title='Cohort360 API')

schema_view = get_schema_view(
    openapi.Info(
        title="Cohort 360",
        default_version='v2.3',
        description="Infos de l'API concernant Cohort 360",
        terms_of_service="",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

internal_urls = [
]

urlpatterns = [
    url(r'^', include(router.urls)),
    path("explorations/", include(('explorations.urls', 'explorations'), namespace="explorations")),
    url(r'^docs', schema_view.with_ui('swagger', cache_timeout=0, )),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^old-docs/', old_schema_view),
    url(r'^accounts/', include('cohort.urls')),
#    url(r'^accounts/', include('rest_framework.urls')),
    url(r'^search/criteria/$', SearchCriteria.as_view(), name="search_criteria"),
    url(r'^voting/create-issue', IssuePost.as_view(), name='voting_issues'),
    # url(r'^voting/thumbs', Thumbs.as_view(), name='voting_thumbs'),
    # url(r'^groups/<str:name>/add/<str:username>$', SearchCriteria.as_view(), name="search_criteria"),
]
