"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from base.views import (
    CeleryHealthCheckAPIView,
    CompleteMultipartUploadAPIView,
    CreateMultipartUploadAPIView,
    CreatePresignedURLAPIView,
    GetPresignedURLAPIView,
    GetPresignedURLForMultipartUploadAPIView,
    HealthCheckAPIView,
)
from modules.urls import urlpatterns as module_urlpatterns

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health-check-api"),
    path(
        "celery/health-check/",
        CeleryHealthCheckAPIView.as_view(),
        name="celery-health-check-api",
    ),
    path("api/general/authentication/", include("modules.user.authentication.urls")),
    # Media upload related URLs
    path(
        "api/general/upload/create-presigned-url/",
        CreatePresignedURLAPIView.as_view(),
        name="create-presigned-url-api",
    ),
    path(
        "api/general/upload/get-presigned-url/",
        GetPresignedURLAPIView.as_view(),
        name="get-presigned-url-api",
    ),
    path(
        "api/general/upload/multipart-upload/",
        CreateMultipartUploadAPIView.as_view(),
        name="create-multipart-upload-api",
    ),
    path(
        "api/general/upload/multipart-upload/get-presigned-url/",
        GetPresignedURLForMultipartUploadAPIView.as_view(),
        name="get-presigned-url-for-multipart-upload-api",
    ),
    path(
        "api/general/upload/multipart-upload/complete/",
        CompleteMultipartUploadAPIView.as_view(),
        name="complete-multipart-upload-api",
    ),
    # Module URLs
    path("api/", include((module_urlpatterns, "modules"), namespace="modules")),
    # Testing URLs
    path("api/testing/", include("modules.testing.urls")),
]
