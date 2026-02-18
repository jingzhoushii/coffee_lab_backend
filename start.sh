#!/bin/bash
# Railway 启动脚本 - 运行时执行数据库迁移

echo "🚀 Starting Coffee Lab Backend..."

# 运行数据库迁移
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# 收集静态文件
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# 启动 Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn coffee_lab_backend.wsgi:application --bind 0.0.0.0:$PORT
