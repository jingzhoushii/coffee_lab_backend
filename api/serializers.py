from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Origin, CoffeeBean, UserRecord, Achievement, UserAchievement, UserCoffeeInventory

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'email', 'avatar', 'bio', 'created_at', 'stats']
        read_only_fields = ['id', 'created_at']
    
    def get_stats(self, obj):
        """获取用户统计"""
        from .services.achievement_service import AchievementService
        service = AchievementService(obj)
        return service.get_user_stats()


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'nickname']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('两次密码输入不一致')
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class OriginSerializer(serializers.ModelSerializer):
    """产地序列化器"""
    is_unlocked = serializers.SerializerMethodField()
    discovered_count = serializers.SerializerMethodField()
    total_coffees = serializers.SerializerMethodField()
    
    class Meta:
        model = Origin
        fields = [
            'id', 'name', 'code', 'latitude', 'longitude',
            'description', 'history', 'industry_status', 'flavor_profile',
            'image_url', 'video_url',
            'is_unlocked', 'discovered_count', 'total_coffees'
        ]
    
    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserRecord.objects.filter(
                user=request.user,
                coffee_bean__origin=obj
            ).exists()
        return False
    
    def get_discovered_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserRecord.objects.filter(
                user=request.user,
                coffee_bean__origin=obj
            ).values('coffee_bean').distinct().count()
        return 0
    
    def get_total_coffees(self, obj):
        return obj.coffee_beans.filter(is_active=True).count()


class CoffeeBeanListSerializer(serializers.ModelSerializer):
    """咖啡豆列表序列化器"""
    origin_name = serializers.CharField(source='origin.name', read_only=True)
    is_discovered = serializers.SerializerMethodField()
    
    class Meta:
        model = CoffeeBean
        fields = [
            'id', 'name', 'origin_name', 'region', 'variety',
            'process', 'altitude_display', 'flavor_notes',
            'is_discovered'
        ]
    
    def get_is_discovered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserRecord.objects.filter(
                user=request.user,
                coffee_bean=obj
            ).exists()
        return False


class CoffeeBeanDetailSerializer(serializers.ModelSerializer):
    """咖啡豆详情序列化器"""
    origin = OriginSerializer(read_only=True)
    is_discovered = serializers.SerializerMethodField()
    
    class Meta:
        model = CoffeeBean
        fields = [
            'id', 'name', 'origin', 'region', 'variety',
            'process', 'altitude_min', 'altitude_max', 'altitude_display',
            'flavor_notes', 'description',
            'brewing_methods', 'grind_size', 'ratio', 'temperature', 'brew_time',
            'data_source', 'source_url',
            'is_discovered', 'created_at'
        ]
    
    def get_is_discovered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserRecord.objects.filter(
                user=request.user,
                coffee_bean=obj
            ).exists()
        return False


class UserRecordSerializer(serializers.ModelSerializer):
    """用户记录序列化器 - 扩展版"""
    coffee_bean = CoffeeBeanListSerializer(read_only=True)
    coffee_bean_id = serializers.IntegerField(write_only=True)
    flavor_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRecord
        fields = [
            'id', 'coffee_bean', 'coffee_bean_id',
            'photo', 'rating', 'notes',
            # 冲煮参数
            'brewing_method', 'grind_size', 'grind_setting',
            'coffee_weight', 'water_weight', 'ratio',
            'water_temperature', 'bloom_time', 'total_time',
            'water_type', 'tds', 'extraction_yield',
            'brewing_params',
            # 口味评价
            'acidity', 'sweetness', 'bitterness', 'body', 'aftertaste', 'balance',
            'flavor_tags', 'flavor_profile',
            # 其他
            'checkin_type', 'recognized_by_ocr', 'ocr_confidence',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'recognized_by_ocr', 'ocr_confidence']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def get_flavor_profile(self, obj):
        """返回风味轮廓数据"""
        return obj.get_flavor_profile()


class UserRecordCreateSerializer(serializers.ModelSerializer):
    """用户记录创建序列化器 - 扩展版"""
    coffee_bean_id = serializers.IntegerField()
    
    class Meta:
        model = UserRecord
        fields = [
            'coffee_bean_id', 'photo', 'rating', 'notes',
            # 冲煮参数
            'brewing_method', 'grind_size', 'grind_setting',
            'coffee_weight', 'water_weight', 'ratio',
            'water_temperature', 'bloom_time', 'total_time',
            'water_type', 'tds', 'extraction_yield',
            'brewing_params',
            # 口味评价
            'acidity', 'sweetness', 'bitterness', 'body', 'aftertaste', 'balance',
            'flavor_tags',
            # 其他
            'checkin_type'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        coffee_bean_id = validated_data.pop('coffee_bean_id')
        validated_data['coffee_bean_id'] = coffee_bean_id
        
        # 检查是否已存在记录
        existing = UserRecord.objects.filter(
            user=validated_data['user'],
            coffee_bean_id=coffee_bean_id
        ).first()
        
        if existing:
            # 更新现有记录
            for key, value in validated_data.items():
                if value is not None:  # 只更新非空值
                    setattr(existing, key, value)
            existing.save()
            return existing
        
        return super().create(validated_data)


class AchievementSerializer(serializers.ModelSerializer):
    """成就序列化器"""
    is_unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon',
            'category', 'rarity', 'condition',
            'is_unlocked', 'unlocked_at'
        ]
    
    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAchievement.objects.filter(
                user=request.user,
                achievement=obj
            ).exists()
        return False
    
    def get_unlocked_at(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user_achievement = UserAchievement.objects.filter(
                user=request.user,
                achievement=obj
            ).first()
            if user_achievement:
                return user_achievement.unlocked_at
        return None


class UserAchievementSerializer(serializers.ModelSerializer):
    """用户成就序列化器"""
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'unlocked_at']


class RecognitionResultSerializer(serializers.Serializer):
    """识别结果序列化器"""
    coffee = CoffeeBeanListSerializer()
    confidence = serializers.FloatField()
    matched_keywords = serializers.ListField(child=serializers.CharField())


class OCRRequestSerializer(serializers.Serializer):
    """OCR 请求序列化器"""
    image = serializers.ImageField(required=True)


class SearchQuerySerializer(serializers.Serializer):
    """搜索请求序列化器"""
    q = serializers.CharField(required=True, min_length=1)


class YearlySummarySerializer(serializers.Serializer):
    """年度总结序列化器"""
    year = serializers.IntegerField()
    total_records = serializers.IntegerField()
    unique_coffees = serializers.IntegerField()
    unique_origins = serializers.IntegerField()
    achievements_unlocked = serializers.IntegerField()
    favorite_origin = serializers.CharField(allow_null=True)
    flavor_preferences = serializers.ListField()
    recommended_coffees = CoffeeBeanListSerializer(many=True)


class UserCoffeeInventorySerializer(serializers.ModelSerializer):
    """咖啡豆库存序列化器"""
    coffee_bean = CoffeeBeanListSerializer(read_only=True)
    coffee_bean_id = serializers.IntegerField(write_only=True)
    consumption_percentage = serializers.SerializerMethodField()
    is_fresh = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserCoffeeInventory
        fields = [
            'id', 'coffee_bean', 'coffee_bean_id',
            'purchase_date', 'purchase_price', 'purchase_weight', 'remaining_weight',
            'roast_date', 'best_before_date',
            'status', 'status_display', 'storage_method', 'notes',
            'consumption_percentage', 'is_fresh',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def get_consumption_percentage(self, obj):
        return obj.get_consumption_percentage()
    
    def get_is_fresh(self, obj):
        return obj.is_fresh()


class UserCoffeeInventoryCreateSerializer(serializers.ModelSerializer):
    """咖啡豆库存创建序列化器"""
    coffee_bean_id = serializers.IntegerField()
    
    class Meta:
        model = UserCoffeeInventory
        fields = [
            'coffee_bean_id', 'purchase_date', 'purchase_price', 
            'purchase_weight', 'remaining_weight',
            'roast_date', 'best_before_date',
            'status', 'storage_method', 'notes'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        coffee_bean_id = validated_data.pop('coffee_bean_id')
        validated_data['coffee_bean_id'] = coffee_bean_id
        return super().create(validated_data)
