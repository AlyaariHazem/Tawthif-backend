from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Job URLs
    path('', views.JobListView.as_view(), name='job_list'),
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    path('my-jobs/', views.MyJobsView.as_view(), name='my_jobs'),
    path('categories/', views.JobCategoryListView.as_view(), name='job_categories'),
    path('statistics/', views.job_statistics, name='job_statistics'),
    
    path('bookmarks/', views.BookmarkedJobsView.as_view(), name='bookmarked_jobs'),
    path('<int:job_id>/bookmark/', views.bookmark_job, name='bookmark_job'),
    
    # Job Alert URLs
    path('alerts/', views.JobAlertListCreateView.as_view(), name='job_alerts'),
    path('alerts/<int:pk>/', views.JobAlertDetailView.as_view(), name='job_alert_detail'),

    # Recommended Jobs
    path('recommended/', views.RecommendedJobListView.as_view(), name='recommended_jobs'),

    # Job detail must ALWAYS be last
    path('<slug:slug>/', views.JobDetailView.as_view(), name='job_detail'),
    path('<slug:slug>/update/', views.JobUpdateView.as_view(), name='job_update'),
    path('<slug:slug>/delete/', views.JobDeleteView.as_view(), name='job_delete'),

    path('<int:job_id>/similar/', views.similar_jobs, name='similar_jobs'),
]

