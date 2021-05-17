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
from django.urls import include, path

from rest_framework import routers
from rest_framework_extensions.routers import NestedRouterMixin

from explorations.views import RequestViewSet, RequestQuerySnapshotViewSet, CohortResultViewSet, DatedMeasureViewSet, \
    FolderViewSet


class NestedDefaultRouter(NestedRouterMixin, routers.DefaultRouter):
    pass


router = NestedDefaultRouter()

folder_router = router.register(r'folders', FolderViewSet, basename="folders")
folder_req_router = folder_router.register(
    'requests',
    RequestViewSet,
    basename="folder-requests",
    parents_query_lookups=["parent_folder"]
)

req_router = router.register(r'requests', RequestViewSet, basename="requests")
req_rqs_router = req_router.register(
    'query-snapshots',
    RequestQuerySnapshotViewSet,
    basename="request-request-query-snapshots",
    parents_query_lookups=["request"]
)
folder_req_rqs_router = folder_req_router.register(
    'query-snapshots',
    RequestQuerySnapshotViewSet,
    basename="folder-request-request-query-snapshots",
    parents_query_lookups=["parent_folder", "request"]
)

req_router.register(
    'dated-measures',
    DatedMeasureViewSet,
    basename="request-dated-measures",
    parents_query_lookups=["request"]
)
folder_req_router.register(
    'dated-measures',
    DatedMeasureViewSet,
    basename="folder-request-dated-measures",
    parents_query_lookups=["parent_folder", "request"]
)
req_router.register(
    "cohorts",
    CohortResultViewSet,
    basename="request-cohort-results",
    parents_query_lookups=["request"]
)
folder_req_router.register(
    "cohorts",
    CohortResultViewSet,
    basename="folder-request-cohort-results",
    parents_query_lookups=["parent_folder", "request"]
)

rqs_router = router.register(r'request-query-snapshots', RequestQuerySnapshotViewSet)
rqs_router.register(
    'next-snapshots',
    RequestQuerySnapshotViewSet,
    basename="request-query-snapshot-next-snapshots",
    parents_query_lookups=["previous_snapshot"]
)
rqs_router.register(
    'dated-measures',
    DatedMeasureViewSet,
    basename="request-query-snapshot-dated-measures",
    parents_query_lookups=["request_query_snapshot"]
)
req_rqs_router.register(
    'dated-measures',
    DatedMeasureViewSet,
    basename="request-request-query-snapshot-dated-measures",
    parents_query_lookups=["request", "request_query_snapshot"]
)
rqs_router.register(
    'cohorts',
    CohortResultViewSet,
    basename="request-query-snapshot-cohort-results",
    parents_query_lookups=["request_query_snapshot"]
)
req_rqs_router.register(
    'cohorts',
    CohortResultViewSet,
    basename="request-request-query-snapshot-cohort-results",
    parents_query_lookups=["request", "request_query_snapshot"]
)

router.register(r'dated-measures', DatedMeasureViewSet, basename="dated-measures")
router.register(r'cohorts', CohortResultViewSet, basename="cohort-results")

urlpatterns = [
    path('', include(router.urls)),
]
