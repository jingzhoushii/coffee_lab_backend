from typing import List, Dict, Any
from collections import Counter
from django.db.models import Count, Q
from ..models import (
    User, Origin, CoffeeBean, UserRecord,
    Achievement, UserAchievement
)


class AchievementService:
    """成就服务"""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计"""
        records = UserRecord.objects.filter(user=self.user)
        
        # 基本统计
        total_records = records.count()
        unique_coffees = records.values('coffee_bean').distinct().count()
        
        # 产地统计
        unique_origins = records.values('coffee_bean__origin').distinct().count()
        origin_records = records.values('coffee_bean__origin__name').annotate(
            count=Count('id')
        ).order_by('-count')
        favorite_origin = origin_records[0]['coffee_bean__origin__name'] if origin_records else None
        
        # 品种统计
        unique_varieties = records.values('coffee_bean__variety').distinct().count()
        
        # 处理法统计
        process_records = records.values('coffee_bean__process').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 成就统计
        achievements_unlocked = UserAchievement.objects.filter(user=self.user).count()
        
        # 口味偏好分析
        flavor_counter = Counter()
        for record in records.filter(rating__gte=4):
            for flavor in record.coffee_bean.flavor_notes:
                flavor_counter[flavor] += 1
        
        top_flavors = [
            {'flavor': flavor, 'count': count}
            for flavor, count in flavor_counter.most_common(5)
        ]
        
        return {
            'total_records': total_records,
            'unique_coffees': unique_coffees,
            'unique_origins': unique_origins,
            'unique_varieties': unique_varieties,
            'achievements_unlocked': achievements_unlocked,
            'favorite_origin': favorite_origin,
            'top_flavors': top_flavors,
            'process_breakdown': list(process_records),
        }
    
    def check_achievements(self) -> List[Achievement]:
        """
        检查并解锁成就
        返回新解锁的成就列表
        """
        newly_unlocked = []
        
        # 获取用户已解锁的成就
        unlocked_ids = set(
            UserAchievement.objects.filter(user=self.user)
            .values_list('achievement_id', flat=True)
        )
        
        # 获取所有未解锁的成就
        achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=unlocked_ids)
        
        # 获取用户记录
        records = UserRecord.objects.filter(user=self.user)
        
        for achievement in achievements:
            if self._check_condition(achievement.condition, records):
                UserAchievement.objects.create(
                    user=self.user,
                    achievement=achievement
                )
                newly_unlocked.append(achievement)
        
        return newly_unlocked
    
    def _check_condition(self, condition: Dict, records) -> bool:
        """检查单个成就条件"""
        condition_type = condition.get('type')
        target = condition.get('target')
        
        if condition_type == 'origin_count':
            # 探索产地数量
            unique_origins = records.values('coffee_bean__origin').distinct().count()
            return unique_origins >= target
        
        elif condition_type == 'coffee_count':
            # 发现咖啡数量
            unique_coffees = records.values('coffee_bean').distinct().count()
            return unique_coffees >= target
        
        elif condition_type == 'record_count':
            # 记录数量
            return records.count() >= target
        
        elif condition_type == 'specific_origin':
            # 特定产地
            origin_names = target if isinstance(target, list) else [target]
            for origin_name in origin_names:
                if records.filter(coffee_bean__origin__name=origin_name).exists():
                    return True
            return False
        
        elif condition_type == 'specific_coffee':
            # 特定咖啡
            coffee_ids = target if isinstance(target, list) else [target]
            for coffee_id in coffee_ids:
                if records.filter(coffee_bean_id=coffee_id).exists():
                    return True
            return False
        
        elif condition_type == 'specific_variety':
            # 特定品种
            varieties = target if isinstance(target, list) else [target]
            for variety in varieties:
                if records.filter(coffee_bean__variety__icontains=variety).exists():
                    return True
            return False
        
        elif condition_type == 'specific_process':
            # 特定处理法
            processes = target if isinstance(target, list) else [target]
            for process in processes:
                if records.filter(coffee_bean__process=process).exists():
                    return True
            return False
        
        elif condition_type == 'rating_count':
            # 评分数量
            min_rating = condition.get('min_rating', 4)
            count = records.filter(rating__gte=min_rating).count()
            return count >= target
        
        elif condition_type == 'flavor_explorer':
            # 风味探索者 - 收集特定风味标签
            flavor_tags = target if isinstance(target, list) else [target]
            for tag in flavor_tags:
                if not records.filter(
                    coffee_bean__flavor_notes__contains=[tag]
                ).exists():
                    return False
            return True
        
        elif condition_type == 'high_altitude':
            # 高海拔猎人
            return records.filter(
                coffee_bean__altitude_min__gte=target
            ).exists()
        
        elif condition_type == 'ocr_master':
            # OCR 大师 - 使用 OCR 识别
            return records.filter(recognized_by_ocr=True).count() >= target
        
        return False
    
    def get_recommendations(self, limit: int = 5) -> List[CoffeeBean]:
        """
        根据用户偏好推荐咖啡
        """
        # 获取用户喜欢的风味
        liked_flavors = []
        for record in UserRecord.objects.filter(
            user=self.user,
            rating__gte=4
        ):
            liked_flavors.extend(record.coffee_bean.flavor_notes)
        
        if not liked_flavors:
            # 如果没有评分记录，随机推荐
            return CoffeeBean.objects.filter(
                is_active=True
            ).exclude(
                id__in=UserRecord.objects.filter(user=self.user).values('coffee_bean_id')
            ).order_by('?')[:limit]
        
        # 根据喜欢的风味推荐
        flavor_counter = Counter(liked_flavors)
        top_flavors = [f for f, _ in flavor_counter.most_common(3)]
        
        # 构建查询
        query = Q()
        for flavor in top_flavors:
            query |= Q(flavor_notes__contains=[flavor])
        
        recommendations = CoffeeBean.objects.filter(
            query,
            is_active=True
        ).exclude(
            id__in=UserRecord.objects.filter(user=self.user).values('coffee_bean_id')
        ).distinct()[:limit]
        
        return recommendations
    
    def generate_yearly_summary(self, year: int) -> Dict[str, Any]:
        """生成年度总结"""
        records = UserRecord.objects.filter(
            user=self.user,
            created_at__year=year
        )
        
        if not records.exists():
            return None
        
        # 基本统计
        total_records = records.count()
        unique_coffees = records.values('coffee_bean').distinct().count()
        unique_origins = records.values('coffee_bean__origin').distinct().count()
        
        # 成就统计
        achievements_unlocked = UserAchievement.objects.filter(
            user=self.user,
            unlocked_at__year=year
        ).count()
        
        # 最喜欢的产地
        origin_records = records.values('coffee_bean__origin__name').annotate(
            count=Count('id')
        ).order_by('-count')
        favorite_origin = origin_records[0]['coffee_bean__origin__name'] if origin_records else None
        
        # 口味偏好
        flavor_counter = Counter()
        for record in records.filter(rating__gte=4):
            for flavor in record.coffee_bean.flavor_notes:
                flavor_counter[flavor] += 1
        
        flavor_preferences = [
            {'flavor': flavor, 'count': count}
            for flavor, count in flavor_counter.most_common(5)
        ]
        
        # 推荐咖啡
        recommended = self.get_recommendations(3)
        
        return {
            'year': year,
            'total_records': total_records,
            'unique_coffees': unique_coffees,
            'unique_origins': unique_origins,
            'achievements_unlocked': achievements_unlocked,
            'favorite_origin': favorite_origin,
            'flavor_preferences': flavor_preferences,
            'recommended_coffees': recommended,
        }
