from collections.abc import Iterable
from typing import Any

from celery import current_app
from django.conf import settings
from django.db import IntegrityError, connections, models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from kombu import Connection
from redis import Redis
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
from base.tasks import health_check_task

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
        health_checks: dict[str, Any] = {}

        # Check Redis connectivity
        redis_ok, redis_error = self._check_redis()
        health_checks["redis"] = {
            "status": "up" if redis_ok else "down",
            "error": redis_error,
        }

        # Check database connectivity
        db_health = self._check_databases()
        health_checks["databases"] = db_health

        db_health_ok: bool = all(
            check["status"] == "up" for check in health_checks["databases"].values()
        )

        # Determine overall health status based on individual checks
        overall_ok: bool = all(
            check["status"] == "up" for key, check in health_checks.items() if key != "databases"
        )

        overall_ok = overall_ok and db_health_ok

        return Response(
            {
                "name": "Django WebSocket API",
                "status": "healthy" if overall_ok else "unhealthy",
                "version": "1.0",
                "environment": settings.ENVIRONMENT,
                "health_checks": health_checks,
            }
        )

    def _check_databases(self) -> dict[str, dict[str, str | None]]:
        db_health = {}

        for alias in connections:
            try:
                with connections[alias].cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception as exc:
                db_health[alias] = {
                    "status": "down",
                    "error": str(exc),
                }
            else:
                db_health[alias] = {
                    "status": "up",
                    "error": None,
                }

        return db_health

    def _check_redis(self) -> tuple[bool, str | None]:
        try:
            redis_client = Redis.from_url(settings.REDIS_URL)
            redis_client.ping()
        except Exception as exc:
            return False, str(exc)
        else:
            return True, None


class CeleryHealthCheckAPIView(RetrieveAPIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        health_checks = {}

        # Check if Celery worker can execute tasks
        task_execution_ok, task_execution_error = self._check_task_execution()
        health_checks["task_execution"] = {
            "status": "ok" if task_execution_ok else "error",
            "error": task_execution_error,
        }

        # Check if Celery worker is alive
        worker_alive_ok, worker_alive_error = self._check_worker_alive()
        health_checks["worker_alive"] = {
            "status": "ok" if worker_alive_ok else "error",
            "error": worker_alive_error,
        }

        # Check if Celery can connect to the broker
        broker_connection_ok, broker_connection_error = self._check_broker_connection()
        health_checks["broker_connection"] = {
            "status": "ok" if broker_connection_ok else "error",
            "error": broker_connection_error,
        }

        # Determine overall health status based on individual checks
        overall_ok: bool = all(check["status"] == "ok" for check in health_checks.values())

        return Response(
            {
                "name": "Celery Worker",
                "status": "healthy" if overall_ok else "unhealthy",
                "health_checks": health_checks,
            }
        )

    def _check_task_execution(self) -> tuple[bool, str | None]:
        try:
            result = health_check_task.delay()
            task_result = result.get(timeout=2)  # Wait for up to 2 seconds
        except Exception as exc:
            return False, str(exc)
        else:
            if task_result != "ok":
                return False, f"Unexpected task result: {task_result}"
            return True, None

    def _check_worker_alive(self) -> tuple[bool, str | None]:
        try:
            inspect = current_app.control.inspect()
            response = inspect.ping()
        except Exception as exc:
            return False, str(exc)
        else:
            if not response:
                return False, "No response from worker"
            return True, None

    def _check_broker_connection(self) -> tuple[bool, str | None]:
        try:
            with Connection(settings.CELERY_BROKER_URL, ssl=True) as conn:
                conn.connect()
        except Exception as exc:
            return False, str(exc)
        else:
            return True, None


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
