#!/bin/bash
# Railway 启动脚本 - 简化版先测试

echo "🚀 Starting Coffee Lab Backend..."

# 先只启动服务器测试
exec gunicorn coffee_lab_backend.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
