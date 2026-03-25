import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('امتداد ملف غير مدعوم. الامتدادات المسموحة للصور هي: ') + ', '.join(valid_extensions))

def validate_document_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('امتداد ملف غير مدعوم. الامتدادات المسموحة للمستندات هي: ') + ', '.join(valid_extensions))

def validate_file_extension(value):
    """General validator that allows both images and documents if needed."""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf', '.doc', '.docx', '.txt', '.rtf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('امتداد ملف غير مدعوم.'))
