from django.apps import AppConfig
from django.db.models.signals import post_migrate


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = 'الوظائف'


    def ready(self):
            from .signals import create_default_job_categories
            post_migrate.connect(create_default_job_categories, sender=self)