import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self):
        self.templates = {
            "greeting": "Добро пожаловать в техподдержку Росатом! Чем могу помочь?",
            "fallback": "Понял ваш запрос. Уточните, пожалуйста, детали проблемы.",
            "escalation": "Для решения этого вопроса требуется оператор. Обратитесь по телефону 8-800-xxx-xx-xx"
        }
    
    def generate_from_knowledge(self, kb_result: Dict[str, Any]) -> str:
        """Генерация ответа из базы знаний"""
        return kb_result.get("answer", self.templates["fallback"])
    
    def generate_llm_fallback(self, user_message: str) -> str:
        """Заглушка если LLM недоступен"""
        return f"Запрос: '{user_message}' получен. В настоящее время AI сервис недоступен. Обратитесь к оператору."