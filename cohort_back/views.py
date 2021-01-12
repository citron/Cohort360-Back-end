from rest_framework import status
from rest_framework.response import Response


class NoDeleteViewSetMixin:
    def destroy(self, request, *args, **kwargs):
        return Response({"response": "request_query_snapshot manual deletion not possible"},
                        status=status.HTTP_400_BAD_REQUEST)


class NoUpdateViewSetMixin:
    def update(self, request, *args, **kwargs):
        return Response({"response": "request_query_snapshot manual update not possible"},
                        status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        return Response({"response": "request_query_snapshot manual update not possible"},
                        status=status.HTTP_400_BAD_REQUEST)


