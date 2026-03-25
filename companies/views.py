from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q, Sum
from .models import Company, CompanyReview, CompanyFollower
from .serializers import (
    CompanySerializer, CompanyCreateSerializer, 
    CompanyReviewSerializer, CompanyFollowerSerializer
)
from rest_framework.pagination import PageNumberPagination

class CompanyPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    page_size_query_param = 'page_size'  
    max_page_size = 100

class CompanyListView(generics.ListAPIView):
    """قائمة الشركات مع البحث والفلترة"""
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = CompanyPagination
    filterset_fields = ['size', 'industry', 'city', 'is_verified', 'is_featured']
    search_fields = ['name', 'description', 'industry']
    ordering_fields = ['created_at', 'name', 'employees_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Company.objects.all()
        
        # Filter featured companies
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter verified companies
        verified = self.request.query_params.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        
        return queryset


class CompanyDetailView(generics.RetrieveAPIView):
    """تفاصيل شركة محددة"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class CompanyCreateView(generics.CreateAPIView):
    """إنشاء شركة جديدة"""
    serializer_class = CompanyCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Only employers can create companies
        if self.request.user.user_type != 'employer':
            raise permissions.PermissionDenied("فقط أصحاب العمل يمكنهم إنشاء شركات")
        serializer.save(owner=self.request.user)


class CompanyUpdateView(generics.UpdateAPIView):
    """تحديث شركة"""
    serializer_class = CompanyCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)


class CompanyDeleteView(generics.DestroyAPIView):
    """حذف شركة"""
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)


class MyCompaniesView(generics.ListAPIView):
    """شركاتي"""
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CompanyPagination

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def follow_company(request, company_id):
    """متابعة/إلغاء متابعة شركة"""
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({'error': 'الشركة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
    
    follower, created = CompanyFollower.objects.get_or_create(
        user=request.user, 
        company=company
    )
    
    if not created:
        follower.delete()
        return Response({'message': 'تم إلغاء متابعة الشركة'}, status=status.HTTP_200_OK)
    
    return Response({'message': 'تم متابعة الشركة'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def followed_companies(request):
    """عرض قائمة الشركات التي يتابعها المستخدم"""
    followers = CompanyFollower.objects.filter(user=request.user).select_related('company')

    companies_data = [
        {
            'id': f.company.id,
            'name': f.company.name,
            'logo': f.company.logo.url if f.company.logo else None
        }
        for f in followers
    ]

    return Response({'companies': companies_data}, status=status.HTTP_200_OK)



class FollowedCompaniesView(generics.ListAPIView):
    """الشركات المتابعة"""
    serializer_class = CompanyFollowerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CompanyFollower.objects.filter(
            user=self.request.user
        ).select_related('company').order_by('-followed_at')



class CompanyReviewListView(generics.ListAPIView):
    """قائمة تقييمات شركة"""
    serializer_class = CompanyReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        company_id = self.kwargs['company_id']
        return CompanyReview.objects.filter(
            company_id=company_id, 
            is_approved=True
        ).order_by('-created_at')


class CompanyReviewCreateView(generics.CreateAPIView):
    """إنشاء تقييم شركة"""
    serializer_class = CompanyReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        company_id = self.kwargs['company_id']
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'الشركة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already reviewed this company
        if CompanyReview.objects.filter(company=company, reviewer=request.user).exists():
            return Response(
                {'error': 'لقد قمت بمراجعة هذه الشركة من قبل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=company, reviewer=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def company_statistics(request):
    """إحصائيات الشركات"""
    total_companies = Company.objects.count()
    verified_companies = Company.objects.filter(is_verified=True).count()
    featured_companies = Company.objects.filter(is_featured=True).count()
    
    # Companies by size
    companies_by_size = Company.objects.values('size').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Companies by industry
    companies_by_industry = Company.objects.values('industry').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Companies by city
    companies_by_city = Company.objects.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return Response({
        'total_companies': total_companies,
        'verified_companies': verified_companies,
        'featured_companies': featured_companies,
        'companies_by_size': companies_by_size,
        'companies_by_industry': companies_by_industry,
        'companies_by_city': companies_by_city
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def company_jobs(request, company_id):
    """وظائف شركة محددة"""
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({'error': 'الشركة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
    
    from jobs.serializers import JobListSerializer
    jobs = company.jobs.filter(is_active=True).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    page_size = int(request.query_params.get('page_size', 10))
    page_number = int(request.query_params.get('page', 1))
    
    paginator = Paginator(jobs, page_size)
    page_obj = paginator.get_page(page_number)
    
    serializer = JobListSerializer(page_obj, many=True, context={'request': request})
    
    return Response({
        'jobs': serializer.data,
        'total_count': paginator.count,
        'page_count': paginator.num_pages,
        'current_page': page_number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def top_companies(request):
    """أفضل الشركات"""
    companies = Company.objects.annotate(
        jobs_count=Count('jobs', filter=Q(jobs__is_active=True)),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
    ).filter(jobs_count__gt=0).order_by('-jobs_count', '-avg_rating')[:10]

    serializer = CompanySerializer(companies, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employer_dashboard_stats(request):
    """
    إحصائيات لوحة تحكم صاحب العمل
    """
    if request.user.user_type != 'employer':
        return Response(
            {'error': 'هذه الإحصائيات خاصة بأصحاب العمل فقط'}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # Imports
    from jobs.models import Job
    from applications.models import JobApplication, ApplicationMessage
    from django.db.models.functions import TruncDate
    
    # 1. Basic Counts
    total_companies = Company.objects.filter(owner=request.user).count()
    
    employer_jobs = Job.objects.filter(company__owner=request.user)
    total_jobs = employer_jobs.count()
    active_jobs = employer_jobs.filter(is_active=True).count()
    
    # Applications
    employer_applications = JobApplication.objects.filter(
        job__company__owner=request.user
    )
    total_applications = employer_applications.count()
    
    # Unique Applicants
    total_unique_applicants = employer_applications.values('applicant').distinct().count()
    
    # Views
    total_views = employer_jobs.aggregate(
        total_views=Sum('views_count')
    )['total_views'] or 0

    # Messages
    employer_messages = ApplicationMessage.objects.filter(
        application__job__company__owner=request.user
    )
    total_messages = employer_messages.count()
    
    # Unread messages (received by employer, so sender is not employer)
    unread_messages = employer_messages.filter(
        is_read=False
    ).exclude(sender=request.user).count()

    # 2. Charts Data
    
    # A. Applications Over Time (Last 30 Days or All Time)
    apps_over_time_qs = employer_applications.annotate(
        date=TruncDate('applied_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    apps_over_time = {
        'labels': [item['date'].strftime('%Y-%m-%d') for item in apps_over_time_qs],
        'series': [item['count'] for item in apps_over_time_qs]
    }
    
    # B. Jobs by City
    jobs_by_city_qs = employer_jobs.values('city').annotate(
        count=Count('id')
    ).order_by('-count')
    
    jobs_by_city = {
        'labels': [item['city'] for item in jobs_by_city_qs],
        'series': [item['count'] for item in jobs_by_city_qs]
    }
    
    # C. Jobs by Category
    jobs_by_category_qs = employer_jobs.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    jobs_by_category = {
        'labels': [item['category__name'] or 'غير محدد' for item in jobs_by_category_qs],
        'series': [item['count'] for item in jobs_by_category_qs]
    }
    
    # D. Jobs by Type
    jobs_by_type_qs = employer_jobs.values('job_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    job_type_display = dict(Job.JOB_TYPE_CHOICES)
    jobs_by_type = {
        'labels': [job_type_display.get(item['job_type'], item['job_type']) for item in jobs_by_type_qs],
        'series': [item['count'] for item in jobs_by_type_qs]
    }

    # E. Applications by Status
    applications_by_status_qs = employer_applications.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_display = dict(JobApplication.STATUS_CHOICES)
    applications_by_status = {
        'labels': [status_display.get(item['status'], item['status']) for item in applications_by_status_qs],
        'series': [item['count'] for item in applications_by_status_qs]
    }
    
    # F. Applicants by City (Based on User Profile Location)
    applicants_by_city_qs = employer_applications.values('applicant__location').annotate(
        count=Count('applicant', distinct=True)
    ).order_by('-count')
    
    applicants_by_city = {
        'labels': [item['applicant__location'] or 'غير محدد' for item in applicants_by_city_qs],
        'series': [item['count'] for item in applicants_by_city_qs]
    }

    # G. Applicants by Category
    applicants_by_category_qs = employer_applications.values('job__category__name').annotate(
        count=Count('applicant', distinct=True)
    ).order_by('-count')
    
    applicants_by_category = {
        'labels': [item['job__category__name'] or 'غير محدد' for item in applicants_by_category_qs],
        'series': [item['count'] for item in applicants_by_category_qs]
    }

    # H. Applicants by Job Title
    applicants_by_job_title_qs = employer_applications.values('job__title').annotate(
        count=Count('applicant', distinct=True)
    ).order_by('-count')[:10]  # Top 10 jobs
    
    applicants_by_job_title = {
        'labels': [item['job__title'] for item in applicants_by_job_title_qs],
        'series': [item['count'] for item in applicants_by_job_title_qs]
    }

    return Response({
        'overview': {
            'total_companies': total_companies,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'total_unique_applicants': total_unique_applicants,
            'total_views': total_views,
            'total_messages': total_messages,
            'unread_messages': unread_messages,
        },
        'charts': {
            'apps_over_time': apps_over_time,
            'jobs_by_city': jobs_by_city,
            'jobs_by_category': jobs_by_category,
            'jobs_by_type': jobs_by_type,
            'applications_by_status': applications_by_status,
            'applicants_by_city': applicants_by_city,
            'applicants_by_category': applicants_by_category,
            'applicants_by_job_title': applicants_by_job_title
        }
    })
