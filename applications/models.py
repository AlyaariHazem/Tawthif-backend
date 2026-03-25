from django.db import models
from django.contrib.auth import get_user_model
from jobs.models import Job
from job_forms.models import JobFormQuestion
from core.validators import validate_document_extension, validate_file_extension

User = get_user_model()


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('reviewed', 'تمت المراجعة'),
        ('shortlisted', 'في القائمة المختصرة'),
        ('interview_scheduled', 'تم تحديد موعد المقابلة'),
        ('interview_completed', 'تمت المقابلة'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('withdrawn', 'منسحب'),
        ('external_redirect', 'تم التوجيه لتقديم خارجي'),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='الوظيفة'
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        verbose_name='المتقدم'
    )
    cover_letter = models.TextField(
        blank=True,
        null=True,
        verbose_name='خطاب التقديم'
    )
    resume = models.FileField(
        upload_to='application_resumes/',
        blank=True,
        null=True,
        validators=[validate_document_extension],
        verbose_name='السيرة الذاتية'
    )
    portfolio_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='رابط الأعمال'
    )
    expected_salary = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='الراتب المتوقع'
    )
    availability_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ التوفر'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='الحالة'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    employer_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات صاحب العمل'
    )
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='التقييم'
    )
    is_viewed = models.BooleanField(
        default=False,
        verbose_name='تمت المشاهدة'
    )
    viewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ المشاهدة'
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التقديم'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    # Advanced methods support
    filled_template = models.FileField(
        upload_to='application_filled_templates/',
        blank=True,
        null=True,
        validators=[validate_document_extension],
        verbose_name='الملف المعبأ'
    )
    
    class Meta:
        verbose_name = 'طلب توظيف'
        verbose_name_plural = 'طلبات التوظيف'
        unique_together = ['job', 'applicant']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_accepted(self):
        return self.status == 'accepted'

    @property
    def is_rejected(self):
        return self.status == 'rejected'


class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ('phone', 'مقابلة هاتفية'),
        ('video', 'مقابلة فيديو'),
        ('in_person', 'مقابلة شخصية'),
        ('technical', 'مقابلة تقنية'),
        ('hr', 'مقابلة موارد بشرية'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'مجدولة'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغية'),
        ('rescheduled', 'معاد جدولتها'),
    ]
    
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='طلب التوظيف'
    )
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        verbose_name='نوع المقابلة'
    )
    scheduled_date = models.DateTimeField(
        db_index=True,
        verbose_name='تاريخ المقابلة'
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name='مدة المقابلة (بالدقائق)'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='مكان المقابلة'
    )
    meeting_link = models.URLField(
        blank=True,
        null=True,
        verbose_name='رابط الاجتماع'
    )
    interviewer_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='اسم المقابل'
    )
    interviewer_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='بريد المقابل'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        db_index=True,
        verbose_name='الحالة'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name='التقييم'
    )
    score = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='النتيجة'
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
        verbose_name = 'مقابلة'
        verbose_name_plural = 'المقابلات'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"مقابلة {self.application.applicant.username} - {self.application.job.title}"


class ApplicationMessage(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='طلب التوظيف'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_application_messages',
        verbose_name='المرسل'
    )
    message = models.TextField(
        verbose_name='الرسالة'
    )
    attachment = models.FileField(
        upload_to='application_attachments/',
        blank=True,
        null=True,
        validators=[validate_file_extension],
        verbose_name='مرفق'
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='مقروءة'
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإرسال'
    )
    
    class Meta:
        verbose_name = 'رسالة طلب توظيف'
        verbose_name_plural = 'رسائل طلبات التوظيف'
        ordering = ['sent_at']

    def __str__(self):
        return f"رسالة من {self.sender.username} - {self.application.job.title}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='طلب التوظيف'
    )
    old_status = models.CharField(
        max_length=20,
        choices=JobApplication.STATUS_CHOICES,
        verbose_name='الحالة السابقة'
    )
    new_status = models.CharField(
        max_length=20,
        choices=JobApplication.STATUS_CHOICES,
        verbose_name='الحالة الجديدة'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='تم التغيير بواسطة'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التغيير'
    )
    
    class Meta:
        verbose_name = 'تاريخ حالة طلب التوظيف'
        verbose_name_plural = 'تاريخ حالات طلبات التوظيف'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.application.job.title} - {self.old_status} إلى {self.new_status}"


class ApplicationResponse(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='طلب التوظيف'
    )
    question = models.ForeignKey(
        JobFormQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='السؤال'
    )
    answer_text = models.TextField(blank=True, null=True, verbose_name='الإجابة النصية')
    answer_file = models.FileField(
        upload_to='application_responses/',
        blank=True,
        null=True,
        validators=[validate_file_extension],
        verbose_name='الملف المرفق'
    )

    class Meta:
        verbose_name = 'إجابة طلب'
        verbose_name_plural = 'إجابات الطلبات'
        unique_together = ['application', 'question']

    def __str__(self):
        return f"إجابة {self.application.applicant.username} على {self.question.label}"

