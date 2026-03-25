from django.contrib import admin
from .models import Company, CompanyReview, CompanyFollower


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'size', 'industry', 'is_verified', 'is_featured', 'created_at']
    list_filter = ['size', 'industry', 'city', 'is_verified', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'owner__username']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['owner']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'slug', 'description', 'owner')
        }),
        ('الصور', {
            'fields': ('logo', 'cover_image')
        }),
        ('معلومات الاتصال', {
            'fields': ('website', 'email', 'phone', 'address', 'city', 'country')
        }),
        ('تفاصيل الشركة', {
            'fields': ('size', 'industry', 'founded_year', 'employees_count')
        }),
        ('الحالة', {
            'fields': ('is_verified', 'is_featured')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ['company', 'reviewer', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_current_employee', 'created_at']
    search_fields = ['company__name', 'reviewer__username', 'title', 'review_text']
    raw_id_fields = ['company', 'reviewer']
    readonly_fields = ['created_at']
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"تم الموافقة على {queryset.count()} تقييم")
    approve_reviews.short_description = "الموافقة على التقييمات المحددة"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"تم رفض {queryset.count()} تقييم")
    disapprove_reviews.short_description = "رفض التقييمات المحددة"


@admin.register(CompanyFollower)
class CompanyFollowerAdmin(admin.ModelAdmin):
    list_display = ['company', 'user', 'followed_at']
    list_filter = ['followed_at']
    search_fields = ['company__name', 'user__username']
    raw_id_fields = ['company', 'user']
    readonly_fields = ['followed_at']

