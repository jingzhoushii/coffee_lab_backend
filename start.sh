#!/bin/bash
# Railway 启动脚本

echo "🚀 Starting Coffee Lab Backend..."

# 运行迁移
echo "📦 Running migrations..."
python manage.py migrate --noinput || echo "⚠️ Migration warning"

# 收集静态文件
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️ Static files warning"

# 启动 Gunicorn
echo "🌐 Starting Gunicorn..."
exec gunicorn coffee_lab_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
