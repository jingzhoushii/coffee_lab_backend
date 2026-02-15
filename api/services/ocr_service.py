import hashlib
import re
from typing import List, Dict, Optional, Tuple
from django.db.models import Q
from ..models import CoffeeBean, OCRCache


class OCRService:
    """OCR 识别服务"""
    
    # 停用词
    STOP_WORDS = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那'
    }
    
    # 处理法映射
    PROCESS_MAPPING = {
        '水洗': 'washed',
        'washed': 'washed',
        '日晒': 'natural',
        'natural': 'natural',
        '蜜处理': 'honey',
        'honey': 'honey',
        '湿刨法': 'wet_hulled',
        'wet hulled': 'wet_hulled',
        '厌氧': 'anaerobic',
        'anaerobic': 'anaerobic',
    }
    
    # 品种映射
    VARIETY_MAPPING = {
        '瑰夏': 'geisha',
        'geisha': 'geisha',
        '波旁': 'bourbon',
        'bourbon': 'bourbon',
        '铁皮卡': 'typica',
        'typica': 'typica',
        '卡杜拉': 'caturra',
        'caturra': 'caturra',
        '卡杜艾': 'catuai',
        'catuai': 'catuai',
        '帕卡马拉': 'pacamara',
        'pacamara': 'pacamara',
        'heirloom': 'heirloom',
        '原生种': 'heirloom',
    }
    
    @staticmethod
    def calculate_image_hash(image_data: bytes) -> str:
        """计算图片哈希"""
        return hashlib.md5(image_data).hexdigest()
    
    @classmethod
    def recognize_image(cls, image_data: bytes) -> Tuple[str, float]:
        """
        识别图片中的文字
        返回: (识别文本, 置信度)
        """
        try:
            from google.cloud import vision
            
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_data)
            
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                # 第一个结果是完整的文本
                full_text = texts[0].description
                # 计算平均置信度
                confidences = [text.confidence for text in texts[1:] if hasattr(text, 'confidence')]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
                
                return full_text, avg_confidence
            
            return "", 0.0
            
        except Exception as e:
            print(f"OCR Error: {e}")
            # 如果 Google Cloud Vision 不可用，返回空结果
            return "", 0.0
    
    @classmethod
    def clean_text(cls, text: str) -> List[str]:
        """清洗文本，提取关键词"""
        # 转换为小写
        text = text.lower()
        
        # 移除特殊字符，保留中英文和数字
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词和短词
        keywords = [
            word for word in words
            if len(word) >= 2 and word not in cls.STOP_WORDS
        ]
        
        return keywords
    
    @classmethod
    def search_coffee_beans(cls, keywords: List[str]) -> List[Dict]:
        """
        根据关键词搜索咖啡豆
        返回匹配结果列表，按匹配度排序
        """
        if not keywords:
            return []
        
        results = []
        coffee_beans = CoffeeBean.objects.filter(is_active=True).select_related('origin')
        
        for coffee in coffee_beans:
            score = 0
            matched_keywords = []
            
            coffee_text = f"{coffee.name} {coffee.origin.name} {coffee.region} {coffee.variety}"
            coffee_text_lower = coffee_text.lower()
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # 名称匹配（权重最高）
                if keyword_lower in coffee.name.lower():
                    score += 10
                    matched_keywords.append(keyword)
                    continue
                
                # 产地匹配
                if keyword_lower in coffee.origin.name.lower():
                    score += 8
                    matched_keywords.append(keyword)
                    continue
                
                # 产区匹配
                if keyword_lower in coffee.region.lower():
                    score += 7
                    matched_keywords.append(keyword)
                    continue
                
                # 品种匹配
                if keyword_lower in coffee.variety.lower():
                    score += 6
                    matched_keywords.append(keyword)
                    continue
                
                # 处理法匹配
                if keyword_lower in coffee.get_process_display().lower():
                    score += 5
                    matched_keywords.append(keyword)
                    continue
                
                # 风味标签匹配
                for flavor in coffee.flavor_notes:
                    if keyword_lower in flavor.lower():
                        score += 4
                        matched_keywords.append(keyword)
                        break
            
            if score > 0:
                results.append({
                    'coffee': coffee,
                    'score': score,
                    'confidence': min(score / (len(keywords) * 10), 1.0),
                    'matched_keywords': list(set(matched_keywords))
                })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:5]  # 返回前5个结果
    
    @classmethod
    def recognize_and_search(cls, image_data: bytes, use_cache: bool = True) -> Dict:
        """
        识别图片并搜索咖啡豆
        返回: {
            'text': 识别的原始文本,
            'keywords': 提取的关键词,
            'results': 匹配结果列表,
            'from_cache': 是否来自缓存
        }
        """
        # 计算图片哈希
        image_hash = cls.calculate_image_hash(image_data)
        
        # 检查缓存
        if use_cache:
            cache = OCRCache.objects.filter(image_hash=image_hash).first()
            if cache:
                return {
                    'text': cache.recognized_text,
                    'keywords': cls.clean_text(cache.recognized_text),
                    'results': [{
                        'coffee': cache.matched_coffee,
                        'confidence': cache.confidence,
                        'matched_keywords': []
                    }] if cache.matched_coffee else [],
                    'from_cache': True
                }
        
        # 识别图片
        recognized_text, ocr_confidence = cls.recognize_image(image_data)
        
        if not recognized_text:
            return {
                'text': '',
                'keywords': [],
                'results': [],
                'from_cache': False
            }
        
        # 提取关键词
        keywords = cls.clean_text(recognized_text)
        
        # 搜索咖啡豆
        results = cls.search_coffee_beans(keywords)
        
        # 保存缓存
        if results:
            best_match = results[0]
            OCRCache.objects.update_or_create(
                image_hash=image_hash,
                defaults={
                    'recognized_text': recognized_text,
                    'matched_coffee': best_match['coffee'],
                    'confidence': best_match['confidence']
                }
            )
        
        return {
            'text': recognized_text,
            'keywords': keywords,
            'results': results,
            'from_cache': False
        }
