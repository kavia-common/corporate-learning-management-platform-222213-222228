"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from api.registration import register  # root-level alias forwards to /api/auth/register
from api.auth import UsernameOrEmailTokenObtainPairView  # root-level alias forwards to /api/auth/token
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Root-level aliases for auth to avoid 404s when frontend omits /api
    path('auth/register/', register, name='root_auth_register'),
    path('auth/register', register, name='root_auth_register_no_slash'),
    path('auth/token/', UsernameOrEmailTokenObtainPairView.as_view(), name='root_token_obtain_pair'),
    path('auth/token', UsernameOrEmailTokenObtainPairView.as_view(), name='root_token_obtain_pair_no_slash'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='root_token_refresh'),
    path('auth/token/refresh', TokenRefreshView.as_view(), name='root_token_refresh_no_slash'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='root_token_verify'),
    path('auth/token/verify', TokenVerifyView.as_view(), name='root_token_verify_no_slash'),
    # Primary API namespace
    path('api/', include('api.urls')),
]

schema_view = get_schema_view(
   openapi.Info(
      title="My API",
      default_version='v1',
      description="Test description",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def get_full_url(request):
    scheme = request.scheme
    host = request.get_host()
    forwarded_port = request.META.get("HTTP_X_FORWARDED_PORT")

    if ':' not in host and forwarded_port:
        host = f"{host}:{forwarded_port}"

    return f"{scheme}://{host}"

@csrf_exempt
def dynamic_schema_view(request, *args, **kwargs):
    url = get_full_url(request)
    view = get_schema_view(
        openapi.Info(
            title="My API",
            default_version='v1',
            description="API Docs",
        ),
        public=True,
        url=url,
    )
    return view.with_ui('swagger', cache_timeout=0)(request)

urlpatterns += [
    re_path(r'^docs/$', dynamic_schema_view, name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^swagger\.json$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]