from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Модели данных
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

# Простой классификатор (временно в main.py)
class SimpleClassifier:
    def __init__(self):
        self.keyword_mapping = {
            "пароль": "password_reset",
            "password": "password_reset", 
            "логин": "password_reset",
            "вход": "password_reset",
            "сброс": "password_reset",
            
            "доступ": "access_issues",
            "access": "access_issues", 
            "войти": "access_issues",
            "авторизация": "access_issues",
            
            "принтер": "hardware",
            "печать": "hardware",
            "монитор": "hardware",
            "компьютер": "hardware",
            "оборудование": "hardware",
            
            "почта": "software",
            "email": "software",
            "outlook": "software",
            "программа": "software",
            
            "интернет": "network",
            "сеть": "network", 
            "vpn": "network",
            "wi-fi": "network"
        }
    
    def classify(self, message: str) -> Dict[str, Any]:
        message_lower = message.lower()
        
        category_scores = {}
        for keyword, category in self.keyword_mapping.items():
            if keyword in message_lower:
                category_scores[category] = category_scores.get(category, 0) + 1
        
        if category_scores:
            category = max(category_scores.items(), key=lambda x: x[1])[0]
            confidence = min(sum(category_scores.values()) / 5, 1.0)
        else:
            category = "other"
            confidence = 0.1
        
        if any(word in message_lower for word in ["привет", "здравствуй", "hello", "hi"]):
            confidence = 0.9
            category = "greeting"
        
        return {
            "category": category,
            "confidence": confidence,
            "keywords_found": list(category_scores.keys())
        }

# Простая база знаний (временно в main.py)
class SimpleKnowledgeBase:
    def __init__(self):
        self.solutions = {
            "password_reset": [
                {
                    "question": "сброс пароля",
                    "answer": """Для сброса пароля в корпоративной системе:

1. Перейдите на portal.rosatom.ru/password-reset
2. Введите ваш корпоративный email
3. Подтвердите личность через СМС-код
4. Установите новый пароль

Требования к паролю:
- Не менее 12 символов
- Заглавные и строчные буквы
- Цифры и специальные символы

Если не получается - позвоните в поддержку: 8-800-xxx-xx-xx""",
                    "steps": [
                        "Перейти на портал восстановления пароля",
                        "Ввести корпоративный email",
                        "Подтвердить через СМС",
                        "Установить новый пароль"
                    ],
                    "confidence": 0.9
                }
            ],
            "greeting": [
                {
                    "question": "приветствие",
                    "answer": """Добро пожаловать в систему техподдержки Росатом! 🤖

Я помогу вам с:
• Сбросом паролей
• Проблемами доступа
• Вопросами по оборудованию
• Настройкой ПО

Опишите вашу проблему!""",
                    "steps": [],
                    "confidence": 0.95
                }
            ],
            "hardware": [
                {
                    "question": "проблемы с принтером",
                    "answer": """Устранение проблем с печатью:

1. Проверьте подключение принтера к сети и компьютеру
2. Убедитесь, что принтер выбран по умолчанию
3. Очистите очередь печати
4. Переустановите драйверы принтера""",
                    "steps": [
                        "Проверить подключение принтера",
                        "Выбрать принтер по умолчанию",
                        "Очистить очередь печати",
                        "Переустановить драйверы"
                    ],
                    "confidence": 0.8
                }
            ]
        }
    
    def search(self, query: str, category: str) -> Optional[Dict[str, Any]]:
        query_lower = query.lower()
        
        if category in self.solutions:
            for solution in self.solutions[category]:
                if any(keyword in query_lower for keyword in solution["question"].split()):
                    return solution
        
        for cat_solutions in self.solutions.values():
            for solution in cat_solutions:
                if any(keyword in query_lower for keyword in solution["question"].split()):
                    return solution
        
        return None

# Простой генератор ответов
class SimpleResponseGenerator:
    def __init__(self):
        self.templates = {
            "fallback": "Понял ваш запрос. Уточните, пожалуйста, детали проблемы.",
            "error": "Не удалось обработать запрос. Обратитесь к оператору."
        }
    
    def generate_llm_fallback(self, user_message: str) -> str:
        return f"Запрос: '{user_message}' получен. В настоящее время AI сервис недоступен. Обратитесь к оператору."

# Инициализация компонентов
classifier = SimpleClassifier()
knowledge_base = SimpleKnowledgeBase()
response_gen = SimpleResponseGenerator()

# История тикетов
tickets_history = []

class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "phi3:mini"
    
    def is_available(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, user_message: str, context: Optional[Dict[str, Any]] = None):
        try:
            system_prompt = """Ты - AI-ассистент техподдержки Росатом. Отвечай на русском.
Давай четкие, технические ответы. Если не уверен - предлагай обратиться к оператору."""
            
            if context:
                system_prompt += f"\nКонтекст: {context}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['message']['content']
            else:
                return None
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None

llm_client = LLMClient()

@app.post("/tickets/", response_model=TicketResponse)
async def create_ticket(ticket: TicketRequest):
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        # 1. Классификация
        classification = classifier.classify(ticket.message)
        
        # 2. Поиск в базе знаний
        kb_result = knowledge_base.search(ticket.message, classification["category"])
        
        response_text = ""
        source = "knowledge_base"
        solution_steps = []
        confidence = classification["confidence"]
        
        # 3. Если нашли в базе знаний с высокой уверенностью
        if kb_result and kb_result.get("confidence", 0) > 0.7:
            response_text = kb_result["answer"]
            solution_steps = kb_result.get("steps", [])
            confidence = kb_result["confidence"]
            source = "knowledge_base"
            
        # 4. Если нет - используем LLM
        else:
            if llm_client.is_available():
                # Добавляем контекст из базы знаний если есть (ИСПРАВЛЕНО!)
                context_dict: Dict[str, Any] = {}
                if kb_result is not None:  # Явная проверка на None
                    context_dict = {"similar_solution": kb_result.get("answer", "")}
                
                llm_response = llm_client.generate_response(ticket.message, context_dict)
                if llm_response:
                    response_text = llm_response
                    source = "llm"
                    confidence = 0.6
                else:
                    response_text = response_gen.generate_llm_fallback(ticket.message)
                    source = "error"
                    confidence = 0.1
            else:
                # Если LLM недоступен, используем базовые ответы
                if kb_result is not None:  # Явная проверка на None
                    response_text = kb_result["answer"]
                    confidence = kb_result["confidence"]
                else:
                    response_text = response_gen.templates["fallback"]
                    confidence = 0.3
                source = "knowledge_base"
        
        # 5. Определяем нужен ли человек
        needs_human = (confidence < 0.3 or 
                      len(ticket.message.strip()) < 3 or
                      classification["category"] == "other")
        
        response = TicketResponse(
            ticket_id=ticket_id,
            response=response_text,
            category=classification["category"],
            confidence=confidence,
            source=source,
            needs_human=needs_human,
            solution_steps=solution_steps
        )
        
        # Сохраняем в историю
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
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return TicketResponse(
            ticket_id="ERROR",
            response="Произошла ошибка. Обратитесь к оператору.",
            needs_human=True
        )

@app.get("/tickets/history")
async def get_history():
    return tickets_history

@app.get("/health")
async def health():
    ollama_status = "available" if llm_client.is_available() else "unavailable"
    return {
        "status": "healthy",
        "ollama": ollama_status,
        "tickets_processed": len(tickets_history),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {"message": "AI TechSupport System - Росатом"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)