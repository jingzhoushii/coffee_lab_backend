from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from . import views

class LoginView(APIView):
    """自定义登录视图，返回用户信息和token"""
    permission_classes = []
    
    def post(self, request):
        from django.contrib.auth import authenticate
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response({'detail': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        
        from .serializers import UserSerializer
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

urlpatterns = [
    # 健康检查
    path('health/', views.health_check, name='health-check'),
    
    # 认证
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # 产地
    path('origins/', views.OriginListView.as_view(), name='origin-list'),
    path('origins/<int:pk>/', views.OriginDetailView.as_view(), name='origin-detail'),
    
    # 咖啡豆
    path('coffee/', views.CoffeeBeanListView.as_view(), name='coffee-list'),
    path('coffee/<int:pk>/', views.CoffeeBeanDetailView.as_view(), name='coffee-detail'),
    
    # 识别
    path('recognize/ocr/', views.OCRRecognizeView.as_view(), name='ocr-recognize'),
    path('recognize/search/', views.SearchCoffeeView.as_view(), name='search-coffee'),
    
    # 用户记录
    path('records/', views.UserRecordListCreateView.as_view(), name='record-list-create'),
    path('records/<int:pk>/', views.UserRecordDetailView.as_view(), name='record-detail'),
    path('records/export/', views.ExportRecordsView.as_view(), name='export-records'),
    
    # 成就
    path('achievements/', views.AchievementListView.as_view(), name='achievement-list'),
    path('achievements/my/', views.UserAchievementListView.as_view(), name='user-achievement-list'),
    
    # 咖啡豆库存
    path('inventory/', views.UserCoffeeInventoryListCreateView.as_view(), name='inventory-list-create'),
    path('inventory/<int:pk>/', views.UserCoffeeInventoryDetailView.as_view(), name='inventory-detail'),
    path('inventory/stats/', views.UserCoffeeInventoryStatsView.as_view(), name='inventory-stats'),
    
    # 统计
    path('stats/', views.UserStatsView.as_view(), name='user-stats'),
    path('stats/yearly/', views.YearlySummaryView.as_view(), name='yearly-summary'),
]
