from .classifier import classify_ticket
from .rag_search import search_knowledge_base
from .action_planner import plan_actions
from .response_generator import generate_response

def process_ticket(message: str) -> str:
    category, confidence = classify_ticket(message)
    if confidence < 0.7:
        return "Ваш запрос будет передан оператору."
    
    knowledge_results = search_knowledge_base(message)
    actions = plan_actions(category, knowledge_results)
    
    response = generate_response(actions)
    return response
