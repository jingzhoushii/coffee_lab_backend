from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class User(AbstractUser):
    """扩展 Django 默认用户模型"""
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    bio = models.TextField(blank=True, verbose_name='个人简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return self.nickname or self.username


class Origin(models.Model):
    """咖啡产地"""
    name = models.CharField(max_length=100, unique=True, verbose_name='产地名称')
    code = models.CharField(max_length=10, unique=True, verbose_name='国家代码')
    latitude = models.FloatField(verbose_name='纬度')
    longitude = models.FloatField(verbose_name='经度')
    description = models.TextField(verbose_name='产地描述')
    history = models.TextField(blank=True, verbose_name='发展历程')
    industry_status = models.TextField(blank=True, verbose_name='产业现状')
    flavor_profile = models.TextField(blank=True, verbose_name='风味特征')
    image_url = models.URLField(blank=True, verbose_name='图片URL')
    video_url = models.URLField(blank=True, verbose_name='视频URL')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '产地'
        verbose_name_plural = '产地'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CoffeeBean(models.Model):
    """咖啡豆"""
    PROCESS_CHOICES = [
        ('washed', '水洗'),
        ('natural', '日晒'),
        ('honey', '蜜处理'),
        ('wet_hulled', '湿刨法'),
        ('anaerobic', '厌氧发酵'),
        ('carbonic', '二氧化碳浸渍'),
        ('lactic', '乳酸发酵'),
        ('monsoon', '季风处理'),
        ('other', '其他'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='豆名')
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE, related_name='coffee_beans', verbose_name='产地')
    region = models.CharField(max_length=100, verbose_name='产区')
    variety = models.CharField(max_length=100, verbose_name='品种')
    process = models.CharField(max_length=20, choices=PROCESS_CHOICES, verbose_name='处理法')
    altitude_min = models.IntegerField(null=True, blank=True, verbose_name='最低海拔')
    altitude_max = models.IntegerField(null=True, blank=True, verbose_name='最高海拔')
    flavor_notes = models.JSONField(default=list, verbose_name='风味标签')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 冲煮建议
    brewing_methods = models.JSONField(default=list, verbose_name='推荐冲煮方式')
    grind_size = models.CharField(max_length=50, blank=True, verbose_name='研磨度')
    ratio = models.CharField(max_length=20, blank=True, verbose_name='粉水比')
    temperature = models.CharField(max_length=20, blank=True, verbose_name='水温')
    brew_time = models.CharField(max_length=50, blank=True, verbose_name='冲煮时间')
    
    # 数据来源
    data_source = models.CharField(max_length=200, blank=True, verbose_name='数据来源')
    source_url = models.URLField(blank=True, verbose_name='来源链接')
    
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '咖啡豆'
        verbose_name_plural = '咖啡豆'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.origin.name})"
    
    @property
    def altitude_display(self):
        if self.altitude_min and self.altitude_max:
            return f"{self.altitude_min}-{self.altitude_max}m"
        elif self.altitude_min:
            return f"{self.altitude_min}m+"
        elif self.altitude_max:
            return f"{self.altitude_max}m"
        return ""


class UserRecord(models.Model):
    """用户咖啡记录 - 扩展版"""
    CHECKIN_TYPE_CHOICES = [
        ('brew', '冲煮打卡'),
        ('taste', '品鉴记录'),
        ('purchase', '购买记录'),
        ('wishlist', '想喝清单'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records', verbose_name='用户')
    coffee_bean = models.ForeignKey(CoffeeBean, on_delete=models.CASCADE, related_name='user_records', verbose_name='咖啡豆')
    
    # 照片
    photo = models.ImageField(upload_to='records/%Y/%m/', blank=True, null=True, verbose_name='照片')
    
    # ========== 评分和笔记 ==========
    rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='总体评分'
    )
    notes = models.TextField(blank=True, verbose_name='笔记')
    
    # ========== 详细冲煮参数 ==========
    brewing_method = models.CharField(max_length=50, blank=True, verbose_name='冲煮方式')
    
    # 研磨相关
    grind_size = models.CharField(max_length=50, blank=True, verbose_name='研磨度描述')
    grind_setting = models.CharField(max_length=20, blank=True, verbose_name='研磨刻度')  # 如 "EK43 3.5"
    
    # 粉水比和用量
    coffee_weight = models.FloatField(null=True, blank=True, verbose_name='咖啡粉量(g)')
    water_weight = models.FloatField(null=True, blank=True, verbose_name='注水量(g)')
    ratio = models.CharField(max_length=20, blank=True, verbose_name='粉水比')  # 如 "1:15"
    
    # 水温
    water_temperature = models.IntegerField(null=True, blank=True, verbose_name='水温(°C)')
    
    # 时间参数
    bloom_time = models.IntegerField(null=True, blank=True, verbose_name='闷蒸时间(秒)')
    total_time = models.IntegerField(null=True, blank=True, verbose_name='总萃取时间(秒)')
    
    # 水质
    water_type = models.CharField(max_length=50, blank=True, verbose_name='水质')  # 如 "农夫山泉、过滤水"
    tds = models.FloatField(null=True, blank=True, verbose_name='TDS浓度(ppm)')
    extraction_yield = models.FloatField(null=True, blank=True, verbose_name='萃取率(%)')
    
    # 保留原有 JSON 字段作为扩展
    brewing_params = models.JSONField(default=dict, blank=True, verbose_name='其他冲煮参数')
    
    # ========== 口味评价 (1-10分制) ==========
    acidity = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='酸度'
    )
    sweetness = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='甜度'
    )
    bitterness = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='苦度'
    )
    body = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='醇厚度'
    )
    aftertaste = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='余韵'
    )
    balance = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='平衡度'
    )
    
    # 风味标签 (用户选择的风味)
    flavor_tags = models.JSONField(default=list, blank=True, verbose_name='风味标签')
    
    # 打卡类型
    checkin_type = models.CharField(
        max_length=20,
        choices=CHECKIN_TYPE_CHOICES,
        default='brew',
        verbose_name='打卡类型'
    )
    
    # 识别信息
    recognized_by_ocr = models.BooleanField(default=False, verbose_name='OCR识别')
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name='OCR置信度')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户记录'
        verbose_name_plural = '用户记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.coffee_bean.name}"
    
    def get_flavor_profile(self):
        """获取风味轮廓数据,用于雷达图"""
        return {
            'acidity': self.acidity or 5,
            'sweetness': self.sweetness or 5,
            'bitterness': self.bitterness or 5,
            'body': self.body or 5,
            'aftertaste': self.aftertaste or 5,
            'balance': self.balance or 5,
        }


class Achievement(models.Model):
    """成就"""
    RARITY_CHOICES = [
        ('common', '普通'),
        ('rare', '稀有'),
        ('epic', '史诗'),
        ('legendary', '传说'),
    ]
    
    CATEGORY_CHOICES = [
        ('origin', '产地'),
        ('variety', '品种'),
        ('process', '处理法'),
        ('count', '数量'),
        ('special', '特殊'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='成就名称')
    description = models.TextField(verbose_name='成就描述')
    icon = models.CharField(max_length=50, default='🏆', verbose_name='图标')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='类别')
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common', verbose_name='稀有度')
    
    # 解锁条件 (JSON格式)
    # 例如: {"type": "origin_count", "target": 5}
    # 例如: {"type": "coffee_count", "target": 10}
    # 例如: {"type": "specific_coffee", "target": ["eth-yirgacheffe", "panama-geisha"]}
    condition = models.JSONField(default=dict, verbose_name='解锁条件')
    
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '成就'
        verbose_name_plural = '成就'
        ordering = ['category', 'rarity', 'id']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """用户成就关联"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements', verbose_name='用户')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements', verbose_name='成就')
    unlocked_at = models.DateTimeField(auto_now_add=True, verbose_name='解锁时间')
    
    class Meta:
        verbose_name = '用户成就'
        verbose_name_plural = '用户成就'
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class OCRCache(models.Model):
    """OCR 识别缓存"""
    image_hash = models.CharField(max_length=64, unique=True, verbose_name='图片哈希')
    recognized_text = models.TextField(verbose_name='识别文本')
    matched_coffee = models.ForeignKey(
        CoffeeBean,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='匹配的咖啡'
    )
    confidence = models.FloatField(default=0, verbose_name='置信度')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = 'OCR缓存'
        verbose_name_plural = 'OCR缓存'
    
    def __str__(self):
        return f"OCR Cache {self.image_hash[:16]}..."


class UserCoffeeInventory(models.Model):
    """用户咖啡豆库存管理"""
    STATUS_CHOICES = [
        ('unopened', '未开封'),
        ('opened', '已开封'),
        ('finished', '已喝完'),
        ('discarded', '已丢弃'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coffee_inventory', verbose_name='用户')
    coffee_bean = models.ForeignKey(CoffeeBean, on_delete=models.CASCADE, related_name='inventory_records', verbose_name='咖啡豆')
    
    # 购买信息
    purchase_date = models.DateField(verbose_name='购买日期')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='购买价格(元)')
    purchase_weight = models.FloatField(verbose_name='购买重量(g)')
    remaining_weight = models.FloatField(verbose_name='剩余重量(g)')
    
    # 烘焙日期和赏味期
    roast_date = models.DateField(null=True, blank=True, verbose_name='烘焙日期')
    best_before_date = models.DateField(null=True, blank=True, verbose_name='最佳赏味期至')
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unopened',
        verbose_name='状态'
    )
    
    # 存储信息
    storage_method = models.CharField(max_length=100, blank=True, verbose_name='存储方式')
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '咖啡豆库存'
        verbose_name_plural = '咖啡豆库存'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.coffee_bean.name} ({self.get_status_display()})"
    
    def get_consumption_percentage(self):
        """获取消耗百分比"""
        if self.purchase_weight > 0:
            consumed = self.purchase_weight - self.remaining_weight
            return min(100, max(0, (consumed / self.purchase_weight) * 100))
        return 0
    
    def is_fresh(self):
        """检查是否还在赏味期内"""
        from django.utils import timezone
        if self.best_before_date:
            return timezone.now().date() <= self.best_before_date
        return True
