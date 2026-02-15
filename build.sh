#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Creating superuser if not exists..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee_lab_backend.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
"

echo "Loading initial data..."
python manage.py init_data || echo "Init data command not found or failed, skipping..."

echo "Build completed!"