import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HybridClassifier:
    def __init__(self):
        self.keyword_mapping = {
            "пароль": "password_reset",
            "password": "password_reset", 
            "логин": "password_reset",
            "вход": "password_reset",
            "сброс": "password_reset",
            "учетн": "password_reset",
            
            "доступ": "access_issues",
            "access": "access_issues", 
            "войти": "access_issues",
            "авторизация": "access_issues",
            "permission": "access_issues",
            "права": "access_issues",
            "роль": "access_issues",
            
            "принтер": "hardware",
            "печать": "hardware",
            "printer": "hardware",
            "монитор": "hardware",
            "компьютер": "hardware",
            "ноутбук": "hardware",
            "клавиатура": "hardware",
            "мышь": "hardware",
            "оборудование": "hardware",
            "сканер": "hardware",
            
            "почта": "software",
            "email": "software",
            "outlook": "software",
            "thunderbird": "software",
            "письмо": "software",
            "программа": "software",
            "софт": "software",
            "установк": "software",
            "office": "software",
            "word": "software",
            "excel": "software",
            "1с": "software",
            "sap": "software",
            
            "интернет": "network",
            "сеть": "network", 
            "vpn": "network",
            "wi-fi": "network",
            "wifi": "network",
            "подключение": "network",
            "сайт": "network",
            "браузер": "network",
            "chrome": "network",
            "firefox": "network"
        }
    
    def classify(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        
        # Считаем совпадения по ключевым словам
        category_scores = {}
        for keyword, category in self.keyword_mapping.items():
            if keyword in message_lower:
                category_scores[category] = category_scores.get(category, 0) + 1
        
        # Определяем категорию
        if category_scores:
            category = max(category_scores.items(), key=lambda x: x[1])[0]
            confidence = min(sum(category_scores.values()) / 5, 1.0)
        else:
            category = "other"
            confidence = 0.1
        
        # Приветствие или простой запрос
        if any(word in message_lower for word in ["привет", "здравствуй", "hello", "hi"]):
            confidence = 0.9
            category = "greeting"
        
        # Короткие сообщения
        if len(message.strip()) < 10:
            confidence = max(confidence, 0.8)  # Высокая уверенность для LLM
        
        return {
            "category": category,
            "confidence": confidence,
            "keywords_found": list(category_scores.keys())
        }