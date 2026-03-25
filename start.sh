#!/bin/bash
# python fix_sequence.py.py

# python manage.py makemigrations job_forms
# python manage.py makemigrations jobs
# python manage.py makemigrations applications 

# echo "Making migrations..."
# python manage.py makemigrations

# echo "Applying migrations..."

# python manage.py migrate

# echo "Creating superuser..."
# python create_superuser_script.py

python manage.py collectstatic  
echo "Starting Gunicorn..."
gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:$PORT
