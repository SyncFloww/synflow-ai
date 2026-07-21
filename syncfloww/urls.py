from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # my urls
    path('api/auth/', include('accounts.urls', namespace='accounts')),
    path('api/v1/workspaces/', include('workspaces.urls')),
    path('api/v1/brands/', include('brands.urls')),
    path('api/v1/social/', include('social_accounts.urls')),
    path('api/v1/ai/', include('content_ai.urls')),
    path('api/v1/content/', include('content.urls')),
    path('api/v1/posts/', include('publishing.urls')),
    path('api/v1/activity-logs/', include('observability.urls')),

    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path(
        "",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Optional ReDoc
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
