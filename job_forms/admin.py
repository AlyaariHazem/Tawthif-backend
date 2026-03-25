from django.contrib import admin
from .models import JobForm, JobFormQuestion

class JobFormQuestionInline(admin.TabularInline):
    model = JobFormQuestion
    extra = 1

@admin.register(JobForm)
class JobFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'company')
    search_fields = ('name', 'company__name')
    inlines = [JobFormQuestionInline]
