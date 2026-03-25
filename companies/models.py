from django.db import models
from django.contrib.auth import get_user_model
from core.validators import validate_image_extension

User = get_user_model()


class Company(models.Model):
    COMPANY_SIZE_CHOICES = [
        ('startup', 'ناشئة (1-10 موظفين)'),
        ('small', 'صغيرة (11-50 موظف)'),
        ('medium', 'متوسطة (51-200 موظف)'),
        ('large', 'كبيرة (201-1000 موظف)'),
        ('enterprise', 'مؤسسة (1000+ موظف)'),
    ]
    
    INDUSTRY_CHOICES = [
        ('technology', 'تقنية المعلومات'),
        ('healthcare', 'الرعاية الصحية'),
        ('education', 'التعليم'),
        ('finance', 'المالية والمصرفية'),
        ('construction', 'البناء والتشييد'),
        ('retail', 'التجارة والبيع بالتجزئة'),
        ('manufacturing', 'التصنيع'),
        ('telecommunications', 'الاتصالات'),
        ('other', 'أخرى'),
    ]
    
    name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name='اسم الشركة'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='الرابط المختصر'
    )
    description = models.TextField(
        verbose_name='وصف الشركة'
    )
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        validators=[validate_image_extension],
        verbose_name='شعار الشركة'
    )
    cover_image = models.ImageField(
        upload_to='company_covers/',
        blank=True,
        null=True,
        validators=[validate_image_extension],
        verbose_name='صورة الغلاف'
    )
    website = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='الموقع الإلكتروني',
        help_text='يمكن إدخال www.example.com دون http(s)'
    )

 
    email = models.EmailField(
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    city = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='المدينة'
    )
    country = models.CharField(
        max_length=100,
        default='اليمن',
        verbose_name='البلد'
    )
    size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        db_index=True,
        verbose_name='حجم الشركة'
    )
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        db_index=True,
        verbose_name='القطاع'
    )
    founded_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='سنة التأسيس'
    )
    employees_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='عدد الموظفين'
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='شركة موثقة'
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='شركة مميزة'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_companies',
        verbose_name='المالك'
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
        verbose_name = 'شركة'
        verbose_name_plural = 'الشركات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.website:
            url = self.website.strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'http://' + url
            self.website = url
        super().save(*args, **kwargs)
    
    
    
    def get_absolute_url(self):
        return f"/companies/{self.slug}/"

    @property
    def total_jobs(self):
        return self.jobs.count()

    @property
    def active_jobs(self):
        return self.jobs.filter(is_active=True).count()


class CompanyReview(models.Model):
    RATING_CHOICES = [
        (1, '1 نجمة'),
        (2, '2 نجمة'),
        (3, '3 نجوم'),
        (4, '4 نجوم'),
        (5, '5 نجوم'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='الشركة'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_reviews',
        verbose_name='المراجع'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        db_index=True,
        verbose_name='التقييم'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان المراجعة'
    )
    review_text = models.TextField(
        verbose_name='نص المراجعة'
    )
    pros = models.TextField(
        blank=True,
        null=True,
        verbose_name='الإيجابيات'
    )
    cons = models.TextField(
        blank=True,
        null=True,
        verbose_name='السلبيات'
    )
    is_current_employee = models.BooleanField(
        default=False,
        verbose_name='موظف حالي'
    )
    job_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المسمى الوظيفي'
    )
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='موافق عليه'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    class Meta:
        verbose_name = 'مراجعة شركة'
        verbose_name_plural = 'مراجعات الشركات'
        unique_together = ['company', 'reviewer']
        ordering = ['-created_at']

    def __str__(self):
        return f"مراجعة {self.company.name} بواسطة {self.reviewer.username}"


class CompanyFollower(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='الشركة'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed_companies',
        verbose_name='المستخدم'
    )
    followed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ المتابعة'
    )
    
    class Meta:
        verbose_name = 'متابع شركة'
        verbose_name_plural = 'متابعو الشركات'
        unique_together = ['company', 'user']

    def __str__(self):
        return f"{self.user.username} يتابع {self.company.name}"

