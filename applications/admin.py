from django.contrib import admin
from .models import JobApplication, Interview, ApplicationMessage, ApplicationStatusHistory


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'is_viewed', 'rating', 'applied_at']
    list_filter = ['status', 'is_viewed', 'rating', 'applied_at']
    search_fields = ['applicant__username', 'job__title', 'job__company__name']
    raw_id_fields = ['job', 'applicant']
    readonly_fields = ['applied_at', 'updated_at']
    date_hierarchy = 'applied_at'
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('job', 'applicant', 'status')
        }),
        ('طلب التقديم', {
            'fields': ('cover_letter', 'resume', 'portfolio_url', 'expected_salary', 'availability_date', 'notes')
        }),
        ('تقييم صاحب العمل', {
            'fields': ('employer_notes', 'rating', 'is_viewed', 'viewed_at')
        }),
        ('التواريخ', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_viewed', 'mark_as_pending', 'mark_as_reviewed']
    
    def mark_as_viewed(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_viewed=True, viewed_at=timezone.now())
        self.message_user(request, f"تم تحديد {queryset.count()} طلب كمشاهد")
    mark_as_viewed.short_description = "تحديد كمشاهد"
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f"تم تحديد {queryset.count()} طلب كقيد المراجعة")
    mark_as_pending.short_description = "تحديد كقيد المراجعة"
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
        self.message_user(request, f"تم تحديد {queryset.count()} طلب كتمت المراجعة")
    mark_as_reviewed.short_description = "تحديد كتمت المراجعة"


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'scheduled_date', 'status', 'score', 'created_at']
    list_filter = ['interview_type', 'status', 'scheduled_date', 'created_at']
    search_fields = ['application__applicant__username', 'application__job__title', 'interviewer_name']
    raw_id_fields = ['application']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('معلومات المقابلة', {
            'fields': ('application', 'interview_type', 'scheduled_date', 'duration_minutes', 'status')
        }),
        ('تفاصيل المقابلة', {
            'fields': ('location', 'meeting_link', 'interviewer_name', 'interviewer_email')
        }),
        ('التقييم', {
            'fields': ('notes', 'feedback', 'score')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ApplicationMessage)
class ApplicationMessageAdmin(admin.ModelAdmin):
    list_display = ['application', 'sender', 'message_preview', 'is_read', 'sent_at']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['application__applicant__username', 'application__job__title', 'sender__username', 'message']
    raw_id_fields = ['application', 'sender']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'معاينة الرسالة'


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['application__applicant__username', 'application__job__title', 'changed_by__username']
    raw_id_fields = ['application', 'changed_by']
    readonly_fields = ['changed_at']
    date_hierarchy = 'changed_at'

