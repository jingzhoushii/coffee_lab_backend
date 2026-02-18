#!/bin/bash
# Railway 启动脚本 - 极简版

set -e

echo "🚀 Starting..."

# 先运行检查
echo "🔍 Django check..."
python manage.py check --deploy --fail-level=ERROR 2>&1 || echo "Check warnings (continuing)"

# 运行迁移（关键！）
echo "📦 Migrations..."
python manage.py migrate --noinput 2>&1 || {
    echo "⚠️ Migration failed - database may not be ready"
    echo "Trying to continue anyway..."
}

# 收集静态文件
echo "🎨 Static files..."
python manage.py collectstatic --noinput 2>&1 || echo "Static collection warning"

echo "🌐 Starting server..."
exec gunicorn coffee_lab_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 60
