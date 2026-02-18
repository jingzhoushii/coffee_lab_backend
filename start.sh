#!/bin/bash
# Railway 启动脚本 - 带调试

echo "🚀 Starting Coffee Lab Backend..."
echo "PORT=$PORT"
echo "DATABASE_URL exists: $(if [ -z "$DATABASE_URL" ]; then echo 'NO'; else echo 'YES'; fi)"

# 等待数据库就绪（重试5次）
echo "⏳ Waiting for database..."
for i in {1..5}; do
    python -c "
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
print('✅ Database ready!')
" 2>/dev/null && break
    echo "   Attempt $i/5..."
    sleep 3
done

# 运行迁移
echo "📦 Running migrations..."
python manage.py migrate --noinput || echo "⚠️ Migration warning"

# 收集静态文件
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Static files warning"

# 启动 Gunicorn
echo "🌐 Starting Gunicorn on port $PORT..."
exec gunicorn coffee_lab_backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
