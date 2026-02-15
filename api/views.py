from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
import csv
import json
from datetime import datetime

from .models import Origin, CoffeeBean, UserRecord, Achievement, UserAchievement, UserCoffeeInventory
from .serializers import (
    UserSerializer, UserRegisterSerializer,
    OriginSerializer, CoffeeBeanListSerializer, CoffeeBeanDetailSerializer,
    UserRecordSerializer, UserRecordCreateSerializer,
    AchievementSerializer, UserAchievementSerializer,
    OCRRequestSerializer, SearchQuerySerializer,
    YearlySummarySerializer,
    UserCoffeeInventorySerializer, UserCoffeeInventoryCreateSerializer
)
from .services.ocr_service import OCRService
from .services.achievement_service import AchievementService

User = get_user_model()


# ==================== 用户认证视图 ====================

class RegisterView(generics.CreateAPIView):
    """用户注册"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 生成 JWT token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """用户资料"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


# ==================== 产地视图 ====================

class OriginListView(generics.ListAPIView):
    """产地列表"""
    serializer_class = OriginSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Origin.objects.filter(is_active=True)


class OriginDetailView(generics.RetrieveAPIView):
    """产地详情"""
    queryset = Origin.objects.filter(is_active=True)
    serializer_class = OriginSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'


# ==================== 咖啡豆视图 ====================

class CoffeeBeanListView(generics.ListAPIView):
    """咖啡豆列表"""
    serializer_class = CoffeeBeanListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = CoffeeBean.objects.filter(is_active=True).select_related('origin')
        
        # 搜索功能
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(origin__name__icontains=search) |
                Q(region__icontains=search) |
                Q(variety__icontains=search) |
                Q(flavor_notes__icontains=search)
            )
        
        # 筛选功能
        origin = self.request.query_params.get('origin', '')
        if origin:
            queryset = queryset.filter(origin__name=origin)
        
        process = self.request.query_params.get('process', '')
        if process:
            queryset = queryset.filter(process=process)
        
        variety = self.request.query_params.get('variety', '')
        if variety:
            queryset = queryset.filter(variety__icontains=variety)
        
        return queryset


class CoffeeBeanDetailView(generics.RetrieveAPIView):
    """咖啡豆详情"""
    queryset = CoffeeBean.objects.filter(is_active=True).select_related('origin')
    serializer_class = CoffeeBeanDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ==================== 用户记录视图 ====================

class UserRecordListCreateView(generics.ListCreateAPIView):
    """用户记录列表/创建"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRecordCreateSerializer
        return UserRecordSerializer
    
    def get_queryset(self):
        return UserRecord.objects.filter(
            user=self.request.user
        ).select_related('coffee_bean', 'coffee_bean__origin').order_by('-created_at')
    
    def perform_create(self, serializer):
        record = serializer.save()
        
        # 检查成就解锁
        service = AchievementService(self.request.user)
        newly_unlocked = service.check_achievements()
        
        # 将新解锁的成就添加到响应中
        self.newly_unlocked = newly_unlocked
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        
        response_data = {
            'record': serializer.data,
            'new_achievements': [
                {
                    'id': a.id,
                    'name': a.name,
                    'description': a.description,
                    'icon': a.icon,
                    'rarity': a.rarity
                }
                for a in getattr(self, 'newly_unlocked', [])
            ]
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class UserRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """用户记录详情/更新/删除"""
    serializer_class = UserRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserRecord.objects.filter(user=self.request.user)


# ==================== 识别视图 ====================

class OCRRecognizeView(APIView):
    """OCR 识别"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = OCRRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        image = serializer.validated_data['image']
        image_data = image.read()
        
        # 调用 OCR 服务
        result = OCRService.recognize_and_search(image_data)
        
        # 序列化结果
        from .serializers import RecognitionResultSerializer
        results_data = []
        for item in result['results']:
            results_data.append({
                'coffee': item['coffee'],
                'confidence': item['confidence'],
                'matched_keywords': item['matched_keywords']
            })
        
        return Response({
            'recognized_text': result['text'],
            'keywords': result['keywords'],
            'results': RecognitionResultSerializer(results_data, many=True).data,
            'from_cache': result['from_cache']
        })


class SearchCoffeeView(APIView):
    """搜索咖啡"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': '请提供搜索关键词'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用 OCR 服务的搜索功能
        keywords = OCRService.clean_text(query)
        results = OCRService.search_coffee_beans(keywords)
        
        from .serializers import RecognitionResultSerializer
        results_data = []
        for item in results:
            results_data.append({
                'coffee': item['coffee'],
                'confidence': item['confidence'],
                'matched_keywords': item['matched_keywords']
            })
        
        return Response({
            'query': query,
            'keywords': keywords,
            'results': RecognitionResultSerializer(results_data, many=True).data
        })


# ==================== 成就视图 ====================

class AchievementListView(generics.ListAPIView):
    """成就列表"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Achievement.objects.filter(is_active=True)


class UserAchievementListView(generics.ListAPIView):
    """用户成就列表"""
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAchievement.objects.filter(
            user=self.request.user
        ).select_related('achievement').order_by('-unlocked_at')


# ==================== 统计视图 ====================

class UserStatsView(APIView):
    """用户统计"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        service = AchievementService(request.user)
        stats = service.get_user_stats()
        return Response(stats)


class YearlySummaryView(APIView):
    """年度总结"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        year = request.query_params.get('year')
        if not year:
            year = timezone.now().year
        else:
            year = int(year)
        
        service = AchievementService(request.user)
        summary = service.generate_yearly_summary(year)
        
        if not summary:
            return Response(
                {'message': f'{year}年暂无记录'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(summary)


# ==================== 数据导出视图 ====================

class ExportRecordsView(APIView):
    """导出用户记录"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        format_type = request.query_params.get('format', 'json')
        records = UserRecord.objects.filter(
            user=request.user
        ).select_related('coffee_bean', 'coffee_bean__origin')
        
        if format_type == 'csv':
            response = Response(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="coffee_records_{datetime.now().strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Coffee Name', 'Origin', 'Region', 'Variety', 'Process',
                'Rating', 'Notes', 'Brewing Method', 'Checkin Type', 'Created At'
            ])
            
            for record in records:
                writer.writerow([
                    record.id,
                    record.coffee_bean.name,
                    record.coffee_bean.origin.name,
                    record.coffee_bean.region,
                    record.coffee_bean.variety,
                    record.coffee_bean.get_process_display(),
                    record.rating,
                    record.notes,
                    record.brewing_method,
                    record.get_checkin_type_display(),
                    record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
        
        else:  # JSON format
            data = []
            for record in records:
                data.append({
                    'id': record.id,
                    'coffee': {
                        'name': record.coffee_bean.name,
                        'origin': record.coffee_bean.origin.name,
                        'region': record.coffee_bean.region,
                        'variety': record.coffee_bean.variety,
                        'process': record.coffee_bean.get_process_display(),
                    },
                    'rating': record.rating,
                    'notes': record.notes,
                    'brewing_method': record.brewing_method,
                    'brewing_params': record.brewing_params,
                    'checkin_type': record.get_checkin_type_display(),
                    'created_at': record.created_at.isoformat(),
                })
            
            return Response(data)


# ==================== 咖啡豆库存视图 ====================

class UserCoffeeInventoryListCreateView(generics.ListCreateAPIView):
    """咖啡豆库存列表/创建"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCoffeeInventoryCreateSerializer
        return UserCoffeeInventorySerializer
    
    def get_queryset(self):
        return UserCoffeeInventory.objects.filter(
            user=self.request.user
        ).select_related('coffee_bean', 'coffee_bean__origin').order_by('-created_at')


class UserCoffeeInventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """咖啡豆库存详情/更新/删除"""
    serializer_class = UserCoffeeInventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserCoffeeInventory.objects.filter(user=self.request.user)


class UserCoffeeInventoryStatsView(APIView):
    """咖啡豆库存统计"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        inventory = UserCoffeeInventory.objects.filter(user=request.user)
        
        total_items = inventory.count()
        unopened_count = inventory.filter(status='unopened').count()
        opened_count = inventory.filter(status='opened').count()
        finished_count = inventory.filter(status='finished').count()
        
        # 即将过期的豆子(7天内)
        from django.utils import timezone
        from datetime import timedelta
        expiring_soon = inventory.filter(
            best_before_date__lte=timezone.now().date() + timedelta(days=7),
            best_before_date__gte=timezone.now().date()
        ).count()
        
        # 已过期
        expired = inventory.filter(best_before_date__lt=timezone.now().date()).count()
        
        return Response({
            'total_items': total_items,
            'unopened': unopened_count,
            'opened': opened_count,
            'finished': finished_count,
            'expiring_soon': expiring_soon,
            'expired': expired,
        })


# ==================== 健康检查视图 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """健康检查"""
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })
