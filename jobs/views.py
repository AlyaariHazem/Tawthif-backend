from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Case, When, Value, IntegerField, F
from .models import Job, JobCategory, JobBookmark, JobAlert
from companies.models import CompanyFollower
from applications.models import JobApplication
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateSerializer,
    JobCategorySerializer, JobBookmarkSerializer, JobAlertSerializer
)
from django.utils import timezone

from rest_framework.pagination import PageNumberPagination

class JobPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    page_size_query_param = 'page_size'  
    max_page_size = 100

class JobListView(generics.ListAPIView):
    """قائمة الوظائف مع البحث والفلترة"""
    serializer_class = JobListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = JobPagination
    filterset_fields = ['job_type', 'experience_level', 'city', 'category', 'company']
    search_fields = ['title', 'description', 'skills', 'company__name']
    ordering_fields = ['created_at', 'views_count', 'salary_min']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).select_related('company', 'category')
        
        # Filter by salary range
        salary_min = self.request.query_params.get('salary_min')
        salary_max = self.request.query_params.get('salary_max')
        
        if salary_min:
            queryset = queryset.filter(
                Q(salary_min__gte=salary_min) | Q(salary_min__isnull=True)
            )
        
        if salary_max:
            queryset = queryset.filter(
                Q(salary_max__lte=salary_max) | Q(salary_max__isnull=True)
            )
        
        # Filter featured jobs
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter urgent jobs
        urgent = self.request.query_params.get('urgent')
        if urgent == 'true':
            queryset = queryset.filter(is_urgent=True)
        
        return queryset
        
        
class RecommendedJobListView(generics.ListAPIView):
    """
    قائمة وظائف مقترحة مخصصة للمستخدم
    تعرض الوظائف:
    1. للشركات التي يتابعها المستخدم (الأولوية القصوى)
    2. المشابهة للوظائف التي بحث عنها (من خلال التنبيهات)
    3. المشابهة للوظائف التي تقدم لها سابقاً (نفس الفئة)
    مع استبعاد الوظائف التي تقدم لها بالفعل
    """
    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = JobPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'city', 'category', 'company']
    search_fields = ['title', 'description', 'skills', 'company__name']
    ordering_fields = ['created_at', 'views_count', 'salary_min', 'score']
    
    def get_queryset(self):
        user = self.request.user
        
        # 1. Get IDs of jobs user already applied to (to exclude them)
        applied_job_ids = JobApplication.objects.filter(applicant=user).values_list('job_id', flat=True)
        
        # 2. Get IDs of companies user follows
        followed_company_ids = CompanyFollower.objects.filter(user=user).values_list('company_id', flat=True)
        
        # 3. Get categories of jobs user applied to
        applied_categories_ids = JobApplication.objects.filter(
            applicant=user, 
            job__category__isnull=False
        ).values_list('job__category_id', flat=True).distinct()
        
        # 4. Get active alerts criteria
        alerts = JobAlert.objects.filter(user=user, is_active=True)
        alert_queries = None
        for alert in alerts:
            q = Q()
            if alert.keywords:
                q &= (Q(title__icontains=alert.keywords) | Q(description__icontains=alert.keywords))
            if alert.category:
                q &= Q(category=alert.category)
            if alert.city:
                q &= Q(city=alert.city)
            # Add other filters if needed
            if q:
                if alert_queries is None:
                    alert_queries = q
                else:
                    alert_queries |= q

        # Base QuerySet: Active jobs, excluding applied ones
        queryset = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).exclude(id__in=applied_job_ids)

        # Annotation for scoring
        # Score 3: Followed Company
        # Score 2: Matches Alert
        # Score 1: Matches Category of applied jobs
        
        # Start with Followed Company Score
        score_expression = Case(
            When(company__id__in=followed_company_ids, then=Value(3)),
            default=Value(0),
            output_field=IntegerField(),
        )
        
        # Add Alert Score if queries exist
        if alert_queries:
            score_expression = score_expression + Case(
                When(alert_queries, then=Value(2)),
                default=Value(0),
                output_field=IntegerField(),
            )
            
        # Add Applied Category Score
        score_expression = score_expression + Case(
            When(category__id__in=applied_categories_ids, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        
        queryset = queryset.annotate(
            score=score_expression
        ).order_by('-score', '-created_at')
        
        return queryset


class JobDetailView(generics.RetrieveAPIView):
    """تفاصيل وظيفة محددة"""
    queryset = Job.objects.filter()
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class JobCreateView(generics.CreateAPIView):
    """إنشاء وظيفة جديدة"""
    serializer_class = JobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


class JobUpdateView(generics.UpdateAPIView):
    """تحديث وظيفة"""
    serializer_class = JobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class JobDeleteView(generics.DestroyAPIView):
    """حذف وظيفة"""
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class MyJobsView(generics.ListAPIView):
    """وظائفي المنشورة"""
    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'city', 'category', 'is_active', 'is_featured', 'is_urgent']
    search_fields = ['title', 'description', 'skills']
    ordering_fields = ['created_at', 'views_count', 'salary_min']
    ordering = ['-created_at']
    pagination_class = JobPagination
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


class JobCategoryListView(generics.ListAPIView):
    """قائمة فئات الوظائف مع عدد الوظائف النشطة في كل فئة"""
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        تحسين الاستعلام ليقوم بحساب عدد الوظائف النشطة لكل فئة
        مباشرة من قاعدة البيانات لتجنب مشكلة N+1.
        """
        return JobCategory.objects.filter(is_active=True).annotate(
            jobs_count=Count('jobs', filter=Q(jobs__is_active=True, jobs__application_deadline__gte=timezone.now()))
        ).order_by('-jobs_count', 'name')

class JobBookmarkView(generics.CreateAPIView):
    """حفظ/إلغاء حفظ وظيفة"""
    serializer_class = JobBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BookmarkedJobsView(generics.ListAPIView):
    """الوظائف المحفوظة"""
    serializer_class = JobBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobBookmark.objects.filter(user=self.request.user).order_by('-created_at')

class JobAlertListCreateView(generics.ListCreateAPIView):
    """قائمة وإنشاء تنبيهات الوظائف"""
    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user).order_by('-created_at')

class JobAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """تفاصيل وتحديث وحذف تنبيه وظيفة"""
    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def job_statistics(request):
    """إحصائيات الوظائف"""
    total_jobs = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).count()
    featured_jobs = Job.objects.filter(is_active=True, is_featured=True, application_deadline__gte=timezone.now()).count()
    urgent_jobs = Job.objects.filter(is_active=True, is_urgent=True, application_deadline__gte=timezone.now()).count()
    
    # Jobs by type
    jobs_by_type = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).values('job_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Jobs by city
    jobs_by_city = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Jobs by category
    jobs_by_category = Job.objects.filter(is_active=True, application_deadline__gte=timezone.now()).values(
        'category__name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    return Response({
        'total_jobs': total_jobs,
        'featured_jobs': featured_jobs,
        'urgent_jobs': urgent_jobs,
        'jobs_by_type': jobs_by_type,
        'jobs_by_city': jobs_by_city,
        'jobs_by_category': jobs_by_category
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def similar_jobs(request, job_id):
    """وظائف مشابهة"""
    try:
        job = Job.objects.get(id=job_id, is_active=True)
    except Job.DoesNotExist:
        return Response({'error': 'الوظيفة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
    
    similar_jobs = Job.objects.filter(
        is_active=True, 
        application_deadline__gte=timezone.now(),
        category=job.category
    ).exclude(id=job.id).order_by('-created_at')[:5]
    
    serializer = JobListSerializer(similar_jobs, many=True, context={'request': request})
    return Response(serializer.data)

