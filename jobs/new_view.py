from rest_framework import generics, permissions, status, filters, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Job, JobCategory, JobBookmark, JobAlert
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateSerializer,
    JobCategorySerializer, JobBookmarkSerializer, JobAlertSerializer
)

# -----------------------------
# Serializers for statistics
# -----------------------------
class JobTypeStatSerializer(serializers.Serializer):
    job_type = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()

class JobCityStatSerializer(serializers.Serializer):
    city = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()

class JobCategoryStatSerializer(serializers.Serializer):
    category__name = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()

class JobStatisticsSerializer(serializers.Serializer):
    total_jobs = serializers.IntegerField()
    featured_jobs = serializers.IntegerField()
    urgent_jobs = serializers.IntegerField()
    jobs_by_type = JobTypeStatSerializer(many=True)
    jobs_by_city = JobCityStatSerializer(many=True)
    jobs_by_category = JobCategoryStatSerializer(many=True)


# -----------------------------
# Job list & detail views
# -----------------------------
@extend_schema(
    tags=["Jobs"],
    responses=JobListSerializer(many=True)
)
class JobListView(generics.ListAPIView):
    """قائمة الوظائف مع البحث والفلترة"""
    serializer_class = JobListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'city', 'category', 'company']
    search_fields = ['title', 'description', 'skills', 'company__name']
    ordering_fields = ['created_at', 'views_count', 'salary_min']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True).select_related('company', 'category')
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

        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)

        urgent = self.request.query_params.get('urgent')
        if urgent == 'true':
            queryset = queryset.filter(is_urgent=True)

        return queryset


@extend_schema(
    tags=["Jobs"],
    responses=JobDetailSerializer
)
class JobDetailView(generics.RetrieveAPIView):
    """تفاصيل وظيفة محددة"""
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    tags=["Jobs"],
    request=JobCreateSerializer,
    responses=JobCreateSerializer
)
class JobCreateView(generics.CreateAPIView):
    """إنشاء وظيفة جديدة"""
    serializer_class = JobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


@extend_schema(
    tags=["Jobs"],
    request=JobCreateSerializer,
    responses=JobCreateSerializer
)
class JobUpdateView(generics.UpdateAPIView):
    """تحديث وظيفة"""
    serializer_class = JobCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


@extend_schema(
    tags=["Jobs"],
    responses=OpenApiResponse(description="Job deleted successfully")
)
class JobDeleteView(generics.DestroyAPIView):
    """حذف وظيفة"""
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


@extend_schema(
    tags=["Jobs"],
    responses=JobListSerializer(many=True)
)
class MyJobsView(generics.ListAPIView):
    """وظائفي المنشورة"""
    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).order_by('-created_at')


@extend_schema(
    tags=["Job Categories"],
    responses=JobCategorySerializer(many=True)
)
class JobCategoryListView(generics.ListAPIView):
    """قائمة فئات الوظائف"""
    queryset = JobCategory.objects.filter(is_active=True)
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]


# -----------------------------
# Bookmark Job
# -----------------------------
@extend_schema(
    tags=["Bookmarks"],
    responses={
        200: OpenApiResponse(description="Bookmark toggled successfully"),
        404: OpenApiResponse(description="Job not found")
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bookmark_job(request, job_id):
    """حفظ/إلغاء حفظ وظيفة"""
    try:
        job = Job.objects.get(id=job_id, is_active=True)
    except Job.DoesNotExist:
        return Response({'error': 'الوظيفة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    bookmark, created = JobBookmark.objects.get_or_create(user=request.user, job=job)

    if not created:
        bookmark.delete()
        return Response({'message': 'تم إلغاء حفظ الوظيفة'}, status=status.HTTP_200_OK)

    return Response({'message': 'تم حفظ الوظيفة'}, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Bookmarks"],
    responses=JobBookmarkSerializer(many=True)
)
class BookmarkedJobsView(generics.ListAPIView):
    """الوظائف المحفوظة"""
    serializer_class = JobBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobBookmark.objects.filter(user=self.request.user).order_by('-created_at')


# -----------------------------
# Job Alerts
# -----------------------------
@extend_schema(
    tags=["Job Alerts"],
    responses=JobAlertSerializer(many=True)
)
class JobAlertListCreateView(generics.ListCreateAPIView):
    """قائمة وإنشاء تنبيهات الوظائف"""
    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user).order_by('-created_at')


@extend_schema(
    tags=["Job Alerts"],
    request=JobAlertSerializer,
    responses=JobAlertSerializer
)
class JobAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """تفاصيل وتحديث وحذف تنبيه وظيفة"""
    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user)


# -----------------------------
# Job Statistics
# -----------------------------
@extend_schema(
    tags=["Jobs", "Statistics"],
    responses=JobStatisticsSerializer
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def job_statistics(request):
    """إحصائيات الوظائف"""
    total_jobs = Job.objects.filter(is_active=True).count()
    featured_jobs = Job.objects.filter(is_active=True, is_featured=True).count()
    urgent_jobs = Job.objects.filter(is_active=True, is_urgent=True).count()

    jobs_by_type = list(Job.objects.filter(is_active=True).values('job_type').annotate(
        count=Count('id')
    ).order_by('-count'))

    jobs_by_city = list(Job.objects.filter(is_active=True).values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    jobs_by_category = list(Job.objects.filter(is_active=True).values(
        'category__name'
    ).annotate(count=Count('id')).order_by('-count')[:10])

    return Response({
        'total_jobs': total_jobs,
        'featured_jobs': featured_jobs,
        'urgent_jobs': urgent_jobs,
        'jobs_by_type': jobs_by_type,
        'jobs_by_city': jobs_by_city,
        'jobs_by_category': jobs_by_category
    })


# -----------------------------
# Similar Jobs
# -----------------------------
@extend_schema(
    tags=["Jobs", "Similar"],
    responses=JobListSerializer(many=True)
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def similar_jobs(request, job_id):
    """وظائف مشابهة"""
    try:
        job = Job.objects.get(id=job_id, is_active=True)
    except Job.DoesNotExist:
        return Response({'error': 'الوظيفة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    similar_jobs_qs = Job.objects.filter(
        is_active=True,
        category=job.category
    ).exclude(id=job.id).order_by('-created_at')[:5]

    serializer = JobListSerializer(similar_jobs_qs, many=True, context={'request': request})
    return Response(serializer.data)
