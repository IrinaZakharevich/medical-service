from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Refbook API",
        default_version='v1',
        description="API for managing refbooks, versions and their elements.",
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.BasePermission,),
)

urlpatterns = [
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('admin/', admin.site.urls),
    path('', include('refbooks.urls'))
]
