from typing import List

from django.db import IntegrityError, models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    GenericAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from base.pagination import ItemIndexPagination


class HealthCheckAPIView(RetrieveAPIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "name": "Django WebSocket API",
                "status": "healthy",
                "version": "1.0.0",
                "environment": "development",
            }
        )


class BaseListAPIView(ListModelMixin, GenericAPIView):
    model: type[models.Model]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    pagination_class = ItemIndexPagination
    ordering_fields: List[str] | str = "__all__"

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        # Turn off pagination.
        if self.request.query_params.get("no_pagination", "") == "true":
            self.pagination_class = None

        results = self.model.objects.filter(deleted_at=None).order_by("-created_at")
        return results


class BaseCreateAPIView(CreateAPIView):
    model: type[models.Model]

    def post(self, request, *args, **kwargs):
        try:
            return self.create(request, *args, **kwargs)
        except IntegrityError as exc:
            raise APIException(detail=exc)

    def perform_create(self, serializer):
        return serializer.save(created_at=timezone.now(), created_by=self.request.user.id)


class BaseRetrieveAPIView(RetrieveAPIView):
    model: type[models.Model]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(deleted_at=None)


class BaseUpdateAPIView(UpdateAPIView):
    model: type[models.Model]

    def put(self, request, *args, **kwargs):
        try:
            return self.update(request, *args, **kwargs)
        except IntegrityError as exc:
            raise APIException(detail=exc)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(deleted_at=None)

    def perform_update(self, serializer):
        serializer.save(modified_at=timezone.now(), modified_by=self.request.user.id)


class BaseDestroyAPIView(DestroyAPIView):
    model: type[models.Model]

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user.id
        instance.save()
