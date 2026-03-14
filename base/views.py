from collections.abc import Iterable

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

from base.constants import ViewAction
from base.pagination import ItemIndexPagination

from .permission import IsAuthenticated
from .serializers import (
    CompleteMultipartUploadSerializer,
    CreateMultipartUploadSerializer,
    CreatePresignedURLSerializer,
    GetPresignedURLForMultipartUploadSerializer,
    GetPresignedURLSerializer,
)


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
    model: type[models.Model] | None
    action: str
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    pagination_class: type[ItemIndexPagination] | None = ItemIndexPagination
    ordering_fields: Iterable[str] | str = "__all__"

    def get(self, request, *args, **kwargs):
        self.action = ViewAction.LIST
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        # Turn off pagination.
        if self.request.query_params.get("no_pagination", "") == "true":
            self.pagination_class = None

        if self.model is None:
            raise APIException(detail="Model is not defined for this view.")

        return self.model._default_manager.filter(deleted_at=None).order_by("-created_at")


class BaseCreateAPIView(CreateAPIView):
    model: type[models.Model] | None
    action: str

    def post(self, request, *args, **kwargs):
        try:
            self.action = ViewAction.CREATE
            return self.create(request, *args, **kwargs)
        except IntegrityError as exc:
            raise APIException(detail=str(exc)) from exc

    def perform_create(self, serializer):
        if self.model is None:
            raise APIException(detail="Model is not defined for this view.")

        serializer.save(created_at=timezone.now(), created_by=self.request.user.id)


class BaseRetrieveAPIView(RetrieveAPIView):
    model: type[models.Model] | None
    action: str

    def get(self, request, *args, **kwargs):
        self.action = ViewAction.RETRIEVE
        return self.retrieve(request, *args, **kwargs)

    def get_queryset(self):
        if self.model is None:
            raise APIException(detail="Model is not defined for this view.")

        return self.model._default_manager.filter(deleted_at=None)


class BaseUpdateAPIView(UpdateAPIView):
    model: type[models.Model] | None
    action: str

    def put(self, request, *args, **kwargs):
        try:
            self.action = ViewAction.UPDATE
            return self.update(request, *args, **kwargs)
        except IntegrityError as exc:
            raise APIException(detail=str(exc)) from exc

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_queryset(self):
        if self.model is None:
            raise APIException(detail="Model is not defined for this view.")

        return self.model._default_manager.filter(deleted_at=None)

    def perform_update(self, serializer):
        serializer.save(modified_at=timezone.now(), modified_by=self.request.user.id)


class BaseDestroyAPIView(DestroyAPIView):
    model: type[models.Model] | None
    action: str

    def delete(self, request, *args, **kwargs):
        self.action = ViewAction.DELETE
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user.id
        instance.save()


# Media upload related views
class CreatePresignedURLAPIView(BaseCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model = None
    serializer_class = CreatePresignedURLSerializer


class GetPresignedURLAPIView(BaseCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model = None
    serializer_class = GetPresignedURLSerializer


class CreateMultipartUploadAPIView(BaseCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model = None
    serializer_class = CreateMultipartUploadSerializer


class GetPresignedURLForMultipartUploadAPIView(BaseCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model = None
    serializer_class = GetPresignedURLForMultipartUploadSerializer


class CompleteMultipartUploadAPIView(BaseCreateAPIView):
    permission_classes = (IsAuthenticated,)
    model = None
    serializer_class = CompleteMultipartUploadSerializer
