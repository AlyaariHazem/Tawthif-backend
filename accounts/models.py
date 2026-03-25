from django.db import models
from django.contrib.auth.models import AbstractUser

from django.utils.translation import gettext_lazy as _
from core.validators import validate_image_extension, validate_document_extension

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('job_seeker', 'باحث عن عمل'),
        ('employer', 'صاحب عمل'),
        ('admin', 'مدير'),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='job_seeker',
        db_index=True,
        verbose_name='نوع المستخدم'
    )
    phone = models.CharField(
        max_length=20,
        default="000-000-000",
        unique=True,
        verbose_name='رقم الهاتف'
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الميلاد'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        validators=[validate_image_extension],
        verbose_name='صورة الملف الشخصي'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='نبذة شخصية'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='الموقع'
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='مُتحقق منه'
    )
    verification_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name='كود التحقق'
    )
    verification_code_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت انتهاء صلاحية كود التحقق'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class JobSeekerProfile(models.Model):
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'مبتدئ (0-2 سنة)'),
        ('junior', 'مبتدئ متقدم (2-4 سنوات)'),
        ('mid', 'متوسط (4-7 سنوات)'),
        ('senior', 'خبير (7-10 سنوات)'),
        ('expert', 'خبير متقدم (10+ سنوات)'),
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', 'ثانوية عامة'),
        ('diploma', 'دبلوم'),
        ('bachelor', 'بكالوريوس'),
        ('master', 'ماجستير'),
        ('phd', 'دكتوراه'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='job_seeker_profile',
        verbose_name='المستخدم'
    )
    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True,
        validators=[validate_document_extension],
        verbose_name='السيرة الذاتية'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='مستوى الخبرة'
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='المستوى التعليمي'
    )
    skills = models.TextField(
        blank=True,
        null=True,
        verbose_name='المهارات'
    )
    expected_salary_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الحد الأدنى للراتب المتوقع'
    )
    expected_salary_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الحد الأعلى للراتب المتوقع'
    )
    availability = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='متاح للعمل'
    )
    preferred_job_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='نوع الوظيفة المفضل'
    )
    languages = models.TextField(
        blank=True,
        null=True,
        verbose_name='اللغات'
    )
    
    class Meta:
        verbose_name = 'ملف باحث عن عمل'
        verbose_name_plural = 'ملفات الباحثين عن عمل'

    def __str__(self):
        return f"ملف {self.user.username}"


class EmployerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employer_profile',
        verbose_name='المستخدم'
    )
    company_name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='اسم الشركة'
    )
    company_description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف الشركة'
    )
    company_logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        validators=[validate_image_extension],
        verbose_name='شعار الشركة'
    )
    company_website = models.URLField(
        blank=True,
        null=True,
        verbose_name='موقع الشركة'
    )
    company_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='حجم الشركة'
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='القطاع'
    )
    founded_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='سنة التأسيس'
    )
    
    class Meta:
        verbose_name = 'ملف صاحب عمل'
        verbose_name_plural = 'ملفات أصحاب العمل'

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"


class ProfileDocument(models.Model):
    """وثائق الملف الشخصي للباحثين عن عمل (شهادات، دورات، مشاريع، إلخ)"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('certificate', 'شهادة أكاديمية'),
        ('training', 'شهادة دورة تدريبية'),
        ('project', 'مشروع'),
        ('recommendation', 'خطاب توصية'),
        ('award', 'جائزة أو تكريم'),
        ('other', 'أخرى'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'عام - يمكن لأي صاحب عمل المشاهدة'),
        ('private', 'خاص - فقط أنا'),
        ('employers_only', 'أصحاب العمل فقط - عند التقديم'),
    ]
    
    job_seeker_profile = models.ForeignKey(
        JobSeekerProfile,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='ملف الباحث عن عمل'
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        db_index=True,
        verbose_name='نوع الوثيقة'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='العنوان'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    file = models.FileField(
        upload_to='profile_documents/',
        validators=[validate_document_extension],
        verbose_name='الملف'
    )
    issued_by = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='الجهة المصدرة'
    )
    issue_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الإصدار'
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='employers_only',
        db_index=True,
        verbose_name='مستوى الخصوصية'
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المشاهدات'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'وثيقة ملف شخصي'
        verbose_name_plural = 'وثائق الملفات الشخصية'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.job_seeker_profile.user.username}"
    
    def increment_views(self):
        """زيادة عدد المشاهدات"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class DocumentView(models.Model):
    """تتبع مشاهدات أصحاب العمل للوثائق"""
    
    document = models.ForeignKey(
        ProfileDocument,
        on_delete=models.CASCADE,
        related_name='document_views',
        verbose_name='الوثيقة'
    )
    viewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewed_documents',
        verbose_name='المشاهد'
    )
    application = models.ForeignKey(
        'applications.JobApplication',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_views',
        verbose_name='طلب التوظيف'
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ المشاهدة'
    )
    
    class Meta:
        verbose_name = 'مشاهدة وثيقة'
        verbose_name_plural = 'مشاهدات الوثائق'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.viewer.username} شاهد {self.document.title}"
