from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Origin, CoffeeBean, UserRecord, Achievement, UserAchievement, OCRCache


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'nickname', 'email', 'is_staff', 'created_at']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'nickname', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('额外信息', {'fields': ('nickname', 'avatar', 'bio')}),
    )


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'latitude', 'longitude', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    prepopulated_fields = {'code': ('name',)}


@admin.register(CoffeeBean)
class CoffeeBeanAdmin(admin.ModelAdmin):
    list_display = ['name', 'origin', 'region', 'variety', 'process', 'is_active']
    list_filter = ['process', 'is_active', 'origin']
    search_fields = ['name', 'region', 'variety']


@admin.register(UserRecord)
class UserRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'coffee_bean', 'rating', 'checkin_type', 'created_at']
    list_filter = ['checkin_type', 'rating', 'created_at']
    search_fields = ['user__username', 'coffee_bean__name', 'notes']
    date_hierarchy = 'created_at'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rarity', 'is_active']
    list_filter = ['category', 'rarity', 'is_active']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'unlocked_at']
    list_filter = ['unlocked_at']
    search_fields = ['user__username', 'achievement__name']
    date_hierarchy = 'unlocked_at'


@admin.register(OCRCache)
class OCRCacheAdmin(admin.ModelAdmin):
    list_display = ['image_hash_short', 'matched_coffee', 'confidence', 'created_at']
    readonly_fields = ['image_hash', 'recognized_text']
    
    def image_hash_short(self, obj):
        return obj.image_hash[:16] + '...'
    image_hash_short.short_description = '图片哈希'
