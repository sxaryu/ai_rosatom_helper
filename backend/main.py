import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Конфиг ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI ---
app = FastAPI(
    title="AI TechSupport - Росатом",
    description="Гибридная система с RAG + LLM",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Модели данных ---
class TicketRequest(BaseModel):
    user_id: str
    message: str

class TicketResponse(BaseModel):
    ticket_id: str
    response: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    source: str = "knowledge_base"
    needs_human: bool = False
    solution_steps: Optional[List[str]] = None


# --- Классификатор ---
class SimpleClassifier:
    KEYWORDS = {
        "password_reset": ["пароль", "password", "логин", "вход", "сброс"],
        "access_issues": ["доступ", "access", "войти", "авторизация"],
        "hardware": ["принтер", "печать", "монитор", "компьютер", "оборудование"],
        "software": ["почта", "email", "outlook", "программа"],
        "network": ["интернет", "сеть", "vpn", "wi-fi"],
        "greeting": ["привет", "здравствуй", "hello", "hi"],
        "other": []  # ← добавил категорию other
    }

    def classify(self, message: str) -> Dict[str, Any]:
        msg = message.lower()
        scores = {}
        for cat, keywords in self.KEYWORDS.items():
            scores[cat] = sum(k in msg for k in keywords)
        
        # Если максимальный score = 0, то категория "other"
        category = max(scores.items(), key=lambda x: x[1])[0]
        max_score = scores[category]
        
        if max_score == 0:
            return {"category": "other", "confidence": 0.0}
        
        confidence = min(max_score / 5, 1.0)
        return {"category": category, "confidence": confidence}
# --- База знаний ---
class SimpleKnowledgeBase:
    SOLUTIONS = {
        "password_reset": {
            "triggers": ["пароль", "password", "сброс пароля", "забыл пароль", "восстановление пароля", "логин", "вход", "учетная запись"],
            "answer": """Для сброса пароля:

1. Перейдите на portal.rosatom.ru/password-reset
2. Введите корпоративный email
3. Подтвердите личность через СМС
4. Установите новый пароль

Если проблемы сохраняются, обратитесь в службу поддержки по телефону +7 (495) 123-45-67.""",
            "steps": ["Перейти на портал сброса пароля", "Ввести email", "Подтвердить через СМС", "Установить новый пароль"],
            "confidence": 0.9
        },
        "hardware": {
            "triggers": ["принтер", "печать", "не печатает", "монитор", "компьютер", "оборудование", "клавиатура", "мышь", "картридж", "тонер"],
            "answer": """Устранение проблем с принтером:

1. Проверьте подключение кабелей питания и USB
2. Убедитесь, что принтер включен и нет ошибок на дисплее
3. Проверьте наличие бумаги и картриджа
4. Очистите очередь печати (Панель управления > Устройства > Принтеры)
5. Переустановите драйверы с официального сайта

Для сложных случаев создайте заявку в ITSM.""",
            "steps": ["Проверить подключение", "Проверить питание и бумагу", "Очистить очередь печати", "Переустановить драйверы"],
            "confidence": 0.8
        },
        "software": {
            "triggers": ["почта", "email", "outlook", "программа", "софт", "установка", "удаление", "обновление", "office", "windows"],
            "answer": """Решение проблем с почтой:

1. Проверьте подключение к интернету
2. Перезапустите Outlook
3. Проверьте настройки учетной записи
4. Очистите кеш приложения
5. При необходимости переустановите программу

Для корпоративного ПО используйте центр установки программ.""",
            "steps": ["Проверить интернет", "Перезапустить приложение", "Проверить настройки", "Очистить кеш"],
            "confidence": 0.8
        },
        "network": {
            "triggers": ["интернет", "сеть", "vpn", "wi-fi", "wifi", "подключение", "кабель", "локальная сеть", "интернет не работает"],
            "answer": """Решение сетевых проблем:

1. Проверьте подключение кабеля Ethernet
2. Перезагрузите роутер/коммутатор
3. Проверьте настройки VPN подключения
4. Убедитесь, что Wi-Fi адаптер включен
5. Запустите диагностику сети (правый клик на значке сети)

Для доступа к корпоративной сети используйте Cisco AnyConnect VPN.""",
            "steps": ["Проверить физическое подключение", "Перезагрузить оборудование", "Проверить настройки VPN", "Запустить диагностику"],
            "confidence": 0.8
        },
        "access_issues": {
            "triggers": ["доступ", "access", "войти", "авторизация", "permission", "права доступа", "система недоступна", "доступ запрещен"],
            "answer": """Решение проблем с доступом:

1. Проверьте корректность логина и пароля
2. Убедитесь, что учетная запись активна
3. Проверьте подключение к корпоративной сети
4. Очистите кеш браузера
5. Попробуйте другой браузер

Если проблема сохраняется, обратитесь к системному администратору.""",
            "steps": ["Проверить логин/пароль", "Проверить активность учетной записи", "Очистить кеш браузера", "Попробовать другой браузер"],
            "confidence": 0.8
        },
        "greeting": {
            "triggers": ["привет", "здравствуй", "hello", "hi", "добрый", "начать", "помощь", "help"],
            "answer": """Добро пожаловать в службу технической поддержки Росатом! 🤖

Я помогу вам с:
- Сбросом и восстановлением паролей
- Проблемами с доступом к системам
- Оборудованием (принтеры, компьютеры)
- Программным обеспечением
- Сетевыми подключениями

Опишите вашу проблему, и я постараюсь помочь!""",
            "steps": [],
            "confidence": 0.95
        }
    }

    def search(self, message: str, category: str) -> Optional[Dict[str, Any]]:
        msg = message.lower().strip()
        
        # Сначала ищем точное совпадение по категории
        solution = self.SOLUTIONS.get(category)
        if solution:
            # Проверяем триггеры для этой категории
            triggers = solution.get("triggers", [])
            if any(trigger in msg for trigger in triggers):
                return solution
        
        # Если не нашли по категории, ищем по всем триггерам
        for solution_cat, solution_data in self.SOLUTIONS.items():
            if solution_cat == category:  # Уже проверяли
                continue
                
            triggers = solution_data.get("triggers", [])
            # Требуем более строгого соответствия
            matched_triggers = [trigger for trigger in triggers if trigger in msg]
            
            # Возвращаем решение только если есть значимое совпадение
            if len(matched_triggers) > 0:
                # Для greeting возвращаем только при явных приветствиях
                if solution_cat == "greeting":
                    greeting_words = ["привет", "здравствуй", "hello", "hi", "добрый"]
                    if any(word in msg for word in greeting_words):
                        return solution_data
                else:
                    return solution_data
        
        return None

# --- LLM ---
class LLMClient:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL

    def is_available(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=5).status_code == 200
        except:
            return False

    def generate_response(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        system_prompt = "Ты - AI-ассистент техподдержки Росатом. Отвечай четко. Если не уверен, предлагай обратиться к оператору."
        if context:
            system_prompt += f"\nКонтекст: {context}"
        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "system", "content": system_prompt},
                                 {"role": "user", "content": user_message}],
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            if r.status_code == 200:
                return r.json()['message']['content']
        except Exception as e:
            logger.error(f"LLM error: {e}")
        return None

# --- Ответы ---
class ResponseGenerator:
    FALLBACK = "Понял ваш запрос. Уточните детали проблемы."
    ERROR = "Не удалось обработать запрос. Обратитесь к оператору."

    @staticmethod
    def llm_fallback(message: str) -> str:
        return f"Запрос: '{message}' получен. В настоящее время AI сервис недоступен. Обратитесь к оператору."

# --- Инициализация ---
classifier = SimpleClassifier()
knowledge_base = SimpleKnowledgeBase()
llm_client = LLMClient()
response_gen = ResponseGenerator()
tickets_history: List[Dict[str, Any]] = []

# --- Эндпоинты ---
@app.post("/tickets/", response_model=TicketResponse)
async def create_ticket(ticket: TicketRequest):
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    classification = classifier.classify(ticket.message)
    kb_result = knowledge_base.search(ticket.message, classification["category"])

    response_text = ""
    solution_steps: List[str] = []
    source = "knowledge_base"
    confidence = classification["confidence"]

    if kb_result and kb_result.get("confidence", 0) > 0.7:
        response_text = kb_result["answer"]
        solution_steps = kb_result.get("steps", [])
        confidence = kb_result["confidence"]
    else:
        if llm_client.is_available():
            context = {"similar_solution": kb_result.get("answer")} if kb_result else {}
            llm_response = llm_client.generate_response(ticket.message, context)
            if llm_response:
                response_text = llm_response
                source = "llm"
                confidence = 0.6
            else:
                response_text = response_gen.llm_fallback(ticket.message)
                source = "error"
                confidence = 0.1
        else:
            response_text = kb_result["answer"] if kb_result else response_gen.FALLBACK
            source = "knowledge_base"

    needs_human = confidence < 0.3 or len(ticket.message.strip()) < 3 or classification["category"] == "other"

    response = TicketResponse(
        ticket_id=ticket_id,
        response=response_text,
        category=classification["category"],
        confidence=confidence,
        source=source,
        needs_human=needs_human,
        solution_steps=solution_steps
    )

    tickets_history.append({
        "ticket_id": ticket_id,
        "user_id": ticket.user_id,
        "message": ticket.message,
        "response": response_text,
        "category": classification["category"],
        "source": source,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    })

    logger.info(f"Processed ticket {ticket_id}, source: {source}, category: {classification['category']}")
    return response

@app.get("/tickets/history")
async def get_history():
    return tickets_history

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ollama": "available" if llm_client.is_available() else "unavailable",
        "tickets_processed": len(tickets_history),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {"message": "AI TechSupport System - Росатом"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
