from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'accounts'

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'profile/documents', views.ProfileDocumentViewSet, basename='profile-documents')

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('resend-verification-code/', views.resend_verification_code, name='resend_verification_code'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/job-seeker/', views.update_job_seeker_profile, name='update_job_seeker_profile'),
    path('profile/employer/', views.update_employer_profile, name='update_employer_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', views.confirm_password_reset, name='confirm_password_reset'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    
    # Include router URLs
    path('', include(router.urls)),
]
