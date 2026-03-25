from django.db import models
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class JobForm(models.Model):
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='custom_forms',
        verbose_name='الشركة'
    )
    name = models.CharField(max_length=200, verbose_name='اسم النموذج')
    description = models.TextField(blank=True, null=True, verbose_name='وصف النموذج')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'نموذج تقديم مخصص'
        verbose_name_plural = 'نماذج التقديم المخصصة'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.company.name}"


class JobFormQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'نص قصير'),
        ('textarea', 'نص طويل'),
        ('number', 'رقم'),
        ('select', 'خيار من متعدد'),
        ('checkbox', 'خانة اختيار'),
        ('file', 'ملف مرفق'),
        ('date', 'تاريخ'),
    ]

    form = models.ForeignKey(
        JobForm, 
        on_delete=models.CASCADE, 
        related_name='questions',
        verbose_name='النموذج'
    )
    label = models.CharField(max_length=255, verbose_name='نص السؤال')
    help_text = models.CharField(max_length=255, blank=True, null=True, verbose_name='نص مساعد')
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPE_CHOICES, 
        default='text',
        verbose_name='نوع السؤال'
    )
    required = models.BooleanField(default=True, verbose_name='مطلوب')
    options = models.TextField(
        blank=True, 
        null=True, 
        help_text='أدخل الخيارات مفصولة بفاصلة (فقط لنوع "خيار من متعدد")',
        verbose_name='الخيارات'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'سؤال نموذج'
        verbose_name_plural = 'أسئلة النماذج'
        ordering = ['order']

    def __str__(self):
        return self.label
