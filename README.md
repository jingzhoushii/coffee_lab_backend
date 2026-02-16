# Coffee Lab Backend

Coffee Lab 的后端 API - Django + Django REST Framework 实现。

## 技术栈

- **Django 5.0**
- **Django REST Framework**
- **SQLite**（本地开发）/ **PostgreSQL**（生产环境可选）
- **JWT** 认证
- **CORS** 跨域支持

## 功能模块

- 用户认证（JWT）
- 咖啡数据管理
- 品鉴记录 CRUD
- 成就系统
- 库存管理
- 统计数据 API
- OCR 识别接口（预留）

## 快速开始

### 环境要求
- Python 3.11+
- pip

### 安装

```bash
cd Coffee_Lab/coffee_lab_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

API 地址：http://localhost:8000/api/

管理后台：http://localhost:8000/admin/

## 部署配置

### Railway 部署（SQLite 模式）

项目已配置为使用 SQLite，无需 PostgreSQL。

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 部署
railway up
```

### Render 部署

项目包含 `render.yaml` 配置文件：

1. 推送代码到 GitHub
2. Render 控制台 → New Web Service
3. 连接 GitHub 仓库
4. Render 自动读取配置并部署

### 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `SECRET_KEY` | ✅ | Django 密钥 |
| `DEBUG` | ❌ | 调试模式 (true/false) |
| `ALLOWED_HOSTS` | ❌ | 允许的主机名 |
| `CORS_ALLOWED_ORIGINS` | ❌ | CORS 允许的源 |

## API 文档

### 认证

```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user",
  "password": "pass"
}

# 响应
{
  "user": { ... },
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

### 咖啡列表

```http
GET /api/coffee/
Authorization: Bearer <access_token>

# 查询参数
?search=ethiopia&origin=埃塞俄比亚&process=washed
```

### 记录品鉴

```http
POST /api/records/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "coffee_bean_id": 1,
  "rating": 5,
  "notes": "花香浓郁，酸质明亮",
  "brewing_method": "V60"
}
```

### 完整 API 列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health/` | GET | 健康检查 |
| `/api/auth/register/` | POST | 用户注册 |
| `/api/auth/login/` | POST | 用户登录 |
| `/api/auth/refresh/` | POST | 刷新 Token |
| `/api/auth/profile/` | GET/PUT | 用户资料 |
| `/api/coffee/` | GET | 咖啡列表 |
| `/api/coffee/<id>/` | GET | 咖啡详情 |
| `/api/origins/` | GET | 产地列表 |
| `/api/records/` | GET/POST | 品鉴记录 |
| `/api/records/<id>/` | GET/PUT/DELETE | 记录详情 |
| `/api/achievements/` | GET | 成就列表 |
| `/api/achievements/my/` | GET | 我的成就 |
| `/api/inventory/` | GET/POST | 库存列表 |
| `/api/inventory/<id>/` | GET/PUT/DELETE | 库存详情 |
| `/api/stats/` | GET | 用户统计 |
| `/api/recognize/search/` | POST | 搜索咖啡 |

## 数据库模型

### User（用户）
- username, email, nickname
- avatar, bio
- created_at

### CoffeeBean（咖啡豆）
- name, origin, region
- variety, process
- altitude, flavor_notes
- brewing_methods

### UserRecord（品鉴记录）
- user, coffee_bean
- rating, notes
- brewing_params
- created_at

### Achievement（成就）
- name, description
- icon, category, rarity
- condition

## 开发

### 添加新 API

1. 在 `api/views.py` 创建视图
2. 在 `api/urls.py` 添加路由
3. 在 `api/serializers.py` 创建序列化器

### 运行测试

```bash
python manage.py test
```

## License

MIT