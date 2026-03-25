from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, JobSeekerProfile, EmployerProfile, ProfileDocument, DocumentView


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email','phone', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name','phone']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('user_type', 'phone', 'date_of_birth', 'profile_picture', 'bio', 'location', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('معلومات إضافية'), {
            'fields': ('user_type', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience_level', 'education_level', 'availability', 'expected_salary_min', 'expected_salary_max']
    list_filter = ['experience_level', 'education_level', 'availability']
    search_fields = ['user__username', 'user__email', 'skills']
    raw_id_fields = ['user']


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'company_size', 'industry', 'founded_year']
    list_filter = ['company_size', 'industry']
    search_fields = ['user__username', 'company_name', 'company_description']
    raw_id_fields = ['user']


@admin.register(ProfileDocument)
class ProfileDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'job_seeker_profile', 'visibility', 'views_count', 'issue_date', 'created_at']
    list_filter = ['document_type', 'visibility', 'created_at', 'issue_date']
    search_fields = ['title', 'description', 'issued_by', 'job_seeker_profile__user__username']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    raw_id_fields = ['job_seeker_profile']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الوثيقة', {
            'fields': ('job_seeker_profile', 'document_type', 'title', 'description', 'file')
        }),
        ('معلومات الإصدار', {
            'fields': ('issued_by', 'issue_date')
        }),
        ('إعدادات الخصوصية', {
            'fields': ('visibility', 'views_count')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentView)
class DocumentViewAdmin(admin.ModelAdmin):
    list_display = ['document', 'viewer', 'application', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['document__title', 'viewer__username', 'application__job__title']
    readonly_fields = ['viewed_at']
    raw_id_fields = ['document', 'viewer', 'application']
    date_hierarchy = 'viewed_at'
