from django.db import transaction

def create_default_job_categories(sender, **kwargs):
    from .models import JobCategory

    default_categories = [
        {"slug": "technology", "name": "تقنية المعلومات"},
        {"slug": "marketing", "name": "التسويق"},
        {"slug": "sales", "name": "المبيعات"},
        {"slug": "finance", "name": "المالية والمحاسبة"},
        {"slug": "hr", "name": "الموارد البشرية"},
        {"slug": "engineering", "name": "الهندسة"},
        {"slug": "healthcare", "name": "الرعاية الصحية"},
        {"slug": "education", "name": "التعليم"},
        {"slug": "design", "name": "التصميم"},
        {"slug": "customer-service", "name": "خدمة العملاء"},
    ]

    with transaction.atomic():
        for cat in default_categories:
            JobCategory.objects.get_or_create(
                slug=cat["slug"],
                defaults={
                    "name": cat["name"],
                    "description": "",
                    "is_active": True,
                },
            )
