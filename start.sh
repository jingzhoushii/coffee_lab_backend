#!/bin/bash
# Railway 启动脚本 - 带重试机制

echo "🚀 Starting Coffee Lab Backend..."

# 等待数据库就绪
echo "⏳ Waiting for database..."
for i in {1..30}; do
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffee_lab_backend.settings')
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('Database ready!')
" 2>/dev/null && break
    echo "   Attempt $i/30..."
    sleep 2
done

# 运行数据库迁移
echo "📦 Running database migrations..."
python manage.py migrate --noinput || echo "⚠️  Migration warning (may already exist)"

# 收集静态文件
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static collection warning"

# 启动 Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn coffee_lab_backend.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2
