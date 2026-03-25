from django.contrib import admin
from .models import Job, JobCategory, JobBookmark, JobAlert


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'job_type', 'city', 'experience_level', 'is_active', 'is_featured', 'views_count', 'created_at']
    list_filter = ['job_type', 'experience_level', 'city', 'is_active', 'is_featured', 'is_urgent', 'created_at']
    search_fields = ['title', 'description', 'company__name', 'skills']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['company', 'category', 'posted_by']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'slug', 'description', 'company', 'category', 'posted_by')
        }),
        ('تفاصيل الوظيفة', {
            'fields': ('job_type', 'experience_level', 'education_level', 'city')
        }),
        ('المتطلبات والمهارات', {
            'fields': ('requirements', 'responsibilities', 'benefits', 'skills')
        }),
        ('الراتب', {
            'fields': ('salary_min', 'salary_max', 'is_salary_negotiable')
        }),
        ('معلومات التقديم', {
            'fields': ('application_deadline', 'contact_email', 'contact_phone')
        }),
        ('الحالة', {
            'fields': ('is_active', 'is_featured', 'is_urgent')
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_featured', 'remove_featured', 'make_urgent', 'remove_urgent']
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"تم جعل {queryset.count()} وظيفة مميزة")
    make_featured.short_description = "جعل الوظائف مميزة"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"تم إلغاء تمييز {queryset.count()} وظيفة")
    remove_featured.short_description = "إلغاء تمييز الوظائف"
    
    def make_urgent(self, request, queryset):
        queryset.update(is_urgent=True)
        self.message_user(request, f"تم جعل {queryset.count()} وظيفة عاجلة")
    make_urgent.short_description = "جعل الوظائف عاجلة"
    
    def remove_urgent(self, request, queryset):
        queryset.update(is_urgent=False)
        self.message_user(request, f"تم إلغاء حالة العجلة من {queryset.count()} وظيفة")
    remove_urgent.short_description = "إلغاء حالة العجلة"


@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'job__title']
    raw_id_fields = ['user', 'job']
    readonly_fields = ['created_at']


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'city', 'job_type', 'is_active', 'email_notifications', 'created_at']
    list_filter = ['city', 'job_type', 'is_active', 'email_notifications', 'created_at']
    search_fields = ['user__username', 'title', 'keywords']
    raw_id_fields = ['user', 'category']
    readonly_fields = ['created_at']

