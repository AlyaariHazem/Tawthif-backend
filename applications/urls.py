from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Application URLs
    path('apply/', views.JobApplicationCreateView.as_view(), name='apply_job'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('job-applications/', views.JobApplicationsView.as_view(), name='job_applications'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('<int:pk>/update/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('<int:application_id>/mark-viewed/', views.mark_application_viewed, name='mark_application_viewed'),
    path('<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('statistics/', views.application_statistics, name='application_statistics'),
    
    # Document Access URLs
    path('documents/<int:document_id>/log-view/', views.log_document_view, name='log_document_view'),
    
    # Interview URLs
    path('interviews/', views.InterviewListView.as_view(), name='interview_list'),
    path('interviews/create/', views.InterviewCreateView.as_view(), name='interview_create'),
    path('interviews/<int:pk>/', views.InterviewDetailView.as_view(), name='interview_detail'),
    
    # Message URLs
    path('<int:application_id>/messages/', views.ApplicationMessageListView.as_view(), name='application_messages'),
    path('<int:application_id>/messages/create/', views.ApplicationMessageCreateView.as_view(), name='create_application_message'),
]
