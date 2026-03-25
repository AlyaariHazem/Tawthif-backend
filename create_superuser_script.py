import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal_backend.settings')
django.setup()

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin'

if not User.objects.filter(username=username).exists():
    try:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating superuser: {e}")
else:
    print(f"Superuser '{username}' already exists.")
