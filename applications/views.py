from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from rest_framework import serializers
from .models import JobApplication, Interview, ApplicationMessage, ApplicationStatusHistory
from collections import OrderedDict
from .serializers import (
    JobApplicationSerializer, JobApplicationCreateSerializer, JobApplicationUpdateSerializer,
    JobApplicationDetailSerializer,
    InterviewSerializer, InterviewCreateSerializer, ApplicationMessageSerializer,
    ApplicationStatusHistorySerializer
)


from rest_framework.pagination import PageNumberPagination

class JobApplicationPagination(PageNumberPagination):
    page_size = 50
    page_query_param = 'page'
    page_size_query_param = 'page_size'  
    max_page_size = 100
    
    
class JobApplicationCreateView(generics.CreateAPIView):
    """التقديم لوظيفة"""
    serializer_class = JobApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyApplicationsView(generics.ListAPIView):
    """طلبات التوظيف الخاصة بي"""
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'job__job_type', 'job__city']
    ordering_fields = ['applied_at', 'updated_at']
    ordering = ['-applied_at']
  

    def get_queryset(self):
        return JobApplication.objects.filter(applicant=self.request.user)


class ApplicationDetailView(generics.RetrieveAPIView):
    """تفاصيل طلب توظيف"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        # استخدام السيريالايزر المفصل الذي يتضمن المرفقات
        return JobApplicationDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'job_seeker':
            return JobApplication.objects.filter(applicant=user)
        elif user.user_type == 'employer':
            return JobApplication.objects.filter(job__posted_by=user)
        return JobApplication.objects.none()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # إذا كان صاحب العمل هو من يشاهد الطلب لأول مرة، نحدده كمشاهد
        if request.user.user_type == 'employer' and instance.job.posted_by == request.user:
            if not instance.is_viewed:
                instance.is_viewed = True
                instance.viewed_at = timezone.now()
                instance.save(update_fields=['is_viewed', 'viewed_at'])
                
        return Response(serializer.data)


class ApplicationUpdateView(generics.UpdateAPIView):
    """تحديث طلب توظيف (للموظفين)"""
    serializer_class = JobApplicationUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only employers can update applications
        if self.request.user.user_type != 'employer':
            return JobApplication.objects.none()
        return JobApplication.objects.filter(job__posted_by=self.request.user)


class JobApplicationsView(generics.ListAPIView):
    """طلبات التوظيف للوظائف التي أنشرها"""
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'job', 'is_viewed']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'applicant__username']
    ordering_fields = ['applied_at', 'updated_at', 'rating']
    ordering = ['-applied_at']
    pagination_class = JobApplicationPagination
    
    def get_queryset(self):
        if self.request.user.user_type != 'employer':
            return JobApplication.objects.none()
        return JobApplication.objects.filter(job__posted_by=self.request.user)

    def list(self, request, *args, **kwargs):
        # apply filters/search/ordering first
        queryset = self.filter_queryset(self.get_queryset())

        # compute counts grouped by status for the (filtered) queryset
        status_counts_qs = queryset.values('status').annotate(count=Count('id')).order_by()
        status_counts = {item['status']: item['count'] for item in status_counts_qs}

        # handle pagination-aware response and ensure status_counts appears before "count"
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            # Prepend status_counts to the paginated payload
            new_data = OrderedDict()
            new_data['status_counts'] = status_counts
            for k, v in paginated_response.data.items():
                new_data[k] = v
            paginated_response.data = new_data
            return paginated_response

        # non-paginated fallback
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status_counts': status_counts,
            'results': serializer.data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_application_viewed(request, application_id):
    """تحديد طلب التوظيف كمشاهد"""
    try:
        application = JobApplication.objects.get(
            id=application_id,
            job__posted_by=request.user
        )
    except JobApplication.DoesNotExist:
        return Response({'error': 'طلب التوظيف غير موجود'}, status=status.HTTP_404_NOT_FOUND)
    
    if not application.is_viewed:
        application.is_viewed = True
        application.viewed_at = timezone.now()
        application.save()
    
    return Response({'message': 'تم تحديد الطلب كمشاهد'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def withdraw_application(request, application_id):
    """سحب طلب التوظيف"""
    try:
        application = JobApplication.objects.get(
            id=application_id,
            applicant=request.user
        )
    except JobApplication.DoesNotExist:
        return Response({'error': 'طلب التوظيف غير موجود'}, status=status.HTTP_404_NOT_FOUND)
    
    if application.status in ['accepted', 'rejected']:
        return Response(
            {'error': 'لا يمكن سحب طلب توظيف تم قبوله أو رفضه'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    application.status = 'withdrawn'
    application.save()
    
    # Create status history
    ApplicationStatusHistory.objects.create(
        application=application,
        old_status=application.status,
        new_status='withdrawn',
        changed_by=request.user,
        notes='تم سحب الطلب بواسطة المتقدم'
    )
    
    return Response({'message': 'تم سحب طلب التوظيف'}, status=status.HTTP_200_OK)


# Interview Views
class InterviewListView(generics.ListAPIView):
    """قائمة المقابلات"""
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'interview_type']
    ordering_fields = ['scheduled_date']
    ordering = ['scheduled_date']
    pagination_class = JobApplicationPagination
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'job_seeker':
            return Interview.objects.filter(application__applicant=user)
        elif user.user_type == 'employer':
            return Interview.objects.filter(application__job__posted_by=user)
        return Interview.objects.none()


class InterviewCreateView(generics.CreateAPIView):
    """جدولة مقابلة"""
    serializer_class = InterviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        interview = serializer.save()
        # Update application status
        application = interview.application
        application.status = 'interview_scheduled'
        application.save()


class InterviewDetailView(generics.RetrieveUpdateAPIView):
    """تفاصيل وتحديث مقابلة"""
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'job_seeker':
            return Interview.objects.filter(application__applicant=user)
        elif user.user_type == 'employer':
            return Interview.objects.filter(application__job__posted_by=user)
        return Interview.objects.none()


# Message Views
class ApplicationMessageListView(generics.ListAPIView):
    """رسائل طلب التوظيف"""
    serializer_class = ApplicationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['sent_at']
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        user = self.request.user
        
        # Check if user has access to this application
        try:
            application = JobApplication.objects.get(id=application_id)
            if user != application.applicant and user != application.job.posted_by:
                return ApplicationMessage.objects.none()
        except JobApplication.DoesNotExist:
            return ApplicationMessage.objects.none()
        
        return ApplicationMessage.objects.filter(application_id=application_id)


class ApplicationMessageCreateView(generics.CreateAPIView):
    """إرسال رسالة لطلب التوظيف"""
    serializer_class = ApplicationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        
        # Check if user has access to this application
        try:
            application = JobApplication.objects.get(id=application_id)
            user = self.request.user
            if user != application.applicant and user != application.job.posted_by:
                raise permissions.PermissionDenied("ليس لديك صلاحية للوصول لهذا الطلب")
        except JobApplication.DoesNotExist:
            raise serializers.ValidationError("طلب التوظيف غير موجود")
        
        serializer.save(application=application, sender=self.request.user)


# Statistics Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def application_statistics(request):
    """إحصائيات طلبات التوظيف"""
    user = request.user
    
    if user.user_type == 'job_seeker':
        # Statistics for job seekers
        total_applications = JobApplication.objects.filter(applicant=user).count()
        pending_applications = JobApplication.objects.filter(
            applicant=user, status='pending'
        ).count()
        accepted_applications = JobApplication.objects.filter(
            applicant=user, status='accepted'
        ).count()
        rejected_applications = JobApplication.objects.filter(
            applicant=user, status='rejected'
        ).count()
        
        # Applications by status
        applications_by_status = JobApplication.objects.filter(
            applicant=user
        ).values('status').annotate(count=Count('id'))
        
        return Response({
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'accepted_applications': accepted_applications,
            'rejected_applications': rejected_applications,
            'applications_by_status': applications_by_status
        })
    
    elif user.user_type == 'employer':
        # Statistics for employers
        total_applications = JobApplication.objects.filter(job__posted_by=user).count()
        unviewed_applications = JobApplication.objects.filter(
            job__posted_by=user, is_viewed=False
        ).count()
        pending_applications = JobApplication.objects.filter(
            job__posted_by=user, status='pending'
        ).count()
        
        # Applications by job
        applications_by_job = JobApplication.objects.filter(
            job__posted_by=user
        ).values('job__title').annotate(count=Count('id')).order_by('-count')[:10]
        
        return Response({
            'total_applications': total_applications,
            'unviewed_applications': unviewed_applications,
            'pending_applications': pending_applications,
            'applications_by_job': applications_by_job
        })
    
    return Response({'error': 'نوع المستخدم غير صحيح'}, status=status.HTTP_400_BAD_REQUEST)


# ==================== Document Access Views ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def log_document_view(request, document_id):
    """تسجيل مشاهدة وثيقة بواسطة صاحب عمل"""
    from accounts.models import ProfileDocument, DocumentView
    try:
        document = ProfileDocument.objects.get(id=document_id)
    except ProfileDocument.DoesNotExist:
        return Response({'error': 'الوثيقة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
        
    user = request.user
    if user.user_type != 'employer':
        return Response({'error': 'فقط أصحاب العمل يمكنهم تسجيل مشاهدات الوثائق'}, status=status.HTTP_403_FORBIDDEN)
        
    # محاولة الحصول على طلب التوظيف المرتبط
    application_id = request.data.get('application_id')
    application = None
    if application_id:
        try:
            application = JobApplication.objects.get(id=application_id, job__posted_by=user)
        except JobApplication.DoesNotExist:
            pass
            
    # التحقق من أن صاحب العمل لديه حق الوصول (سواء من خلال طلب توظيف أو إذا كانت الوثيقة عامة)
    if document.visibility == 'private' and document.job_seeker_profile.user != user:
         return Response({'error': 'ليس لديك صلاحية لمشاهدة هذه الوثيقة'}, status=status.HTTP_403_FORBIDDEN)

    # تسجيل المشاهدة
    view_obj, created = DocumentView.objects.get_or_create(
        document=document,
        viewer=user,
        application=application,
        defaults={'viewed_at': timezone.now()}
    )
    
    if created:
        # زيادة عدد المشاهدات الكلي فقط في أول مرة يشاهد فيها هذا صاحب العمل هذه الوثيقة لهذا الطلب
        document.increment_views()
    
    return Response({
        'message': 'تم تسجيل المشاهدة بنجاح',
        'views_count': document.views_count
    }, status=status.HTTP_200_OK)
