from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobFormViewSet

router = DefaultRouter()
router.register('forms', JobFormViewSet, basename='jobform')

urlpatterns = [
    path('', include(router.urls)),
]
