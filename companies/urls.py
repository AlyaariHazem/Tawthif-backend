from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company URLs
    path('', views.CompanyListView.as_view(), name='company_list'),
    path('create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('my-companies/', views.MyCompaniesView.as_view(), name='my_companies'),
    path('statistics/', views.company_statistics, name='company_statistics'),
    path('top/', views.top_companies, name='top_companies'),
    path('employer-dashboard-stats/', views.employer_dashboard_stats, name='employer_dashboard_stats'),  
    # Company Jobs
    path('<int:company_id>/jobs/', views.company_jobs, name='company_jobs'),
    
    # Follow URLs
    path('<int:company_id>/follow/', views.follow_company, name='follow_company'),
    path('followed/', views.FollowedCompaniesView.as_view(), name='followed_companies'),
    
    # Review URLs
    path('<int:company_id>/reviews/', views.CompanyReviewListView.as_view(), name='company_reviews'),
    path('<int:company_id>/reviews/create/', views.CompanyReviewCreateView.as_view(), name='create_company_review'),
    
    path('<slug:slug>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('<slug:slug>/update/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('<slug:slug>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
]

