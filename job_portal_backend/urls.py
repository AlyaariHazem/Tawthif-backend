"""
URL configuration for job_portal_backend project.

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

admin.site.site_header = "إدارة منصة توظيف"
admin.site.site_title = "إدارة منصة توظيف"
admin.site.index_title = "لوحة التحكم"

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API Root - معلومات عن API"""
    return Response({
        'message': 'مرحباً بك في API منصة التوظيف',
        'version': '1.0',
        'endpoints': {
            'accounts': '/api/accounts/',
            'jobs': '/api/jobs/',
            'companies': '/api/companies/',
            'applications': '/api/applications/',
            'job-forms': '/api/job-forms/',
            # 'admin': '/admin/',
        },
        'documentation': 'قريباً...',
        'support': 'support@Tawzif.com'
    })
    
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc UI
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api_root'),
    path('api/accounts/', include('accounts.urls')),
    
    
    
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    
    path('api/jobs/', include('jobs.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/job-forms/', include('job_forms.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

