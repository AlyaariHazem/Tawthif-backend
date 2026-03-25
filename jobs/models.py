from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from companies.models import Company
from job_forms.models import JobForm

User = get_user_model()


class JobCategory(models.Model):
    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='اسم الفئة'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='الرابط المختصر'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='وصف الفئة'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='أيقونة'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='نشط'
    )
    
    class Meta:
        verbose_name = 'فئة وظيفة'
        verbose_name_plural = 'فئات الوظائف'

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'دوام كامل'),
        ('part_time', 'دوام جزئي'),
        ('contract', 'عقد مؤقت'),
        ('freelance', 'عمل حر'),
        ('internship', 'تدريب'),
    ]
    
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
        ('any', 'غير محدد'),
    ]
    
    CITY_CHOICES = [
        ('sanaa', 'صنعاء'),
        ('aden', 'عدن'),
        ('abyan', 'أبين'),
        ('amran', 'عمران'),
        ('al_bayda', 'البيضاء'),
        ('al_hudaydah', 'الحديدة'),
        ('al_jawf', 'الجوف'),
        ('al_maharah', 'المهرة'),
        ('al_mahwit', 'المحويت'),
        ('dhamar', 'ذمار'),
        ('hadhramaut', 'حضرموت'),
        ('hajjah', 'حجة'),
        ('ibb', 'إب'),
        ('lahij', 'لحج'),
        ('marib', 'مأرب'),
        ('raymah', 'ريمة'),
        ('saada', 'صعدة'),
        ('shabwah', 'شبوة'),
        ('socotra', 'سقطرى'),
        ('taiz', 'تعز'),
        ('remote', 'عمل عن بُعد'),
    ]
    
    APPLICATION_METHOD_CHOICES = [
        ('platform', 'النظام الافتراضي للمنصة'),
        ('custom_form', 'استبيان مخصص'),
        ('template_file', 'قالب ملف'),
        ('external_link', 'رابط خارجي'),
        ('email', 'بريد الشركة'),
    ]
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='عنوان الوظيفة'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='الرابط المختصر'
    )
    description = models.TextField(
        verbose_name='وصف الوظيفة'
    )
    requirements = models.TextField(
        verbose_name='متطلبات الوظيفة'
    )
    responsibilities = models.TextField(
        blank=True,
        null=True,
        verbose_name='المسؤوليات'
    )
    benefits = models.TextField(
        blank=True,
        null=True,
        verbose_name='المزايا'
    )
    skills = models.TextField(
        blank=True,
        null=True,
        verbose_name='المهارات المطلوبة'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs',
        verbose_name='الشركة'
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
        verbose_name='الفئة'
    )
    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        db_index=True,
        verbose_name='نوع الوظيفة'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        db_index=True,
        verbose_name='مستوى الخبرة'
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        default='any',
        db_index=True,
        verbose_name='المستوى التعليمي'
    )
    city = models.CharField(
        max_length=50,
        choices=CITY_CHOICES,
        db_index=True,
        verbose_name='المدينة'
    )
    salary_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الحد الأدنى للراتب'
    )
    salary_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الحد الأعلى للراتب'
    )
    is_salary_negotiable = models.BooleanField(
        default=False,
        verbose_name='الراتب قابل للتفاوض'
    )
    application_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='آخر موعد للتقديم'
    )
    contact_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='بريد التواصل'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='هاتف التواصل'
    )
    
    # Advanced Application Methods
    application_method = models.CharField(
        max_length=20,
        choices=APPLICATION_METHOD_CHOICES,
        default='platform',
        verbose_name='طريقة التقديم'
    )
    custom_form = models.ForeignKey(
        JobForm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs',
        verbose_name='الاستبيان المخصص'
    )
    application_template = models.FileField(
        upload_to='job_templates/',
        blank=True,
        null=True,
        verbose_name='قالب طلب التوظيف'
    )
    external_application_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='رابط التقديم الخارجي'
    )
    application_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='بريد التقديم'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='نشط'
    )
       # AI Summary Fields
    is_ai_summary_enabled = models.BooleanField(
        default=False,
        verbose_name='تفعيل تلخيص الذكاء الاصطناعي'
    )
    
    ai_summary = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملخص الذكاء الاصطناعي'
    )
    
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='مميز'
    )
    is_urgent = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='عاجل'
    )
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد المشاهدات'
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
        verbose_name='منشور بواسطة'
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
        verbose_name = 'وظيفة'
        verbose_name_plural = 'الوظائف'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_absolute_url(self):
        return f"/jobs/{self.slug}/"

    @property
    def is_expired(self):
        if self.application_deadline:
            return timezone.now() > self.application_deadline
        return False

    @property
    def applications_count(self):
        return self.applications.count()

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class JobBookmark(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookmarked_jobs',
        verbose_name='المستخدم'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='الوظيفة'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الحفظ'
    )
    
    class Meta:
        verbose_name = 'وظيفة محفوظة'
        verbose_name_plural = 'الوظائف المحفوظة'
        unique_together = ['user', 'job']

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"


class JobAlert(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_alerts',
        verbose_name='المستخدم'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان التنبيه'
    )
    keywords = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='الكلمات المفتاحية'
    )
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الفئة'
    )
    city = models.CharField(
        max_length=50,
        choices=Job.CITY_CHOICES,
        blank=True,
        null=True,
        verbose_name='المدينة'
    )
    job_type = models.CharField(
        max_length=20,
        choices=Job.JOB_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='نوع الوظيفة'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        blank=True,
        null=True,
        verbose_name='مستوى الخبرة'
    )
    salary_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الحد الأدنى للراتب'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='نشط'
    )
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='إشعارات البريد الإلكتروني'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'تنبيه وظيفة'
        verbose_name_plural = 'تنبيهات الوظائف'

    def __str__(self):
        return f"{self.title} - {self.user.username}"

