"""
Роуты для чата с агентами.
Включает OpenAI совместимый endpoint и внутренние API.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from typing import Dict, Any

# Импортируем схемы
from schemas.openai import ChatRequest, ChatResponse, Message

# TODO: Реализовать импорт функций
# from agent.agent_switcher import (
#     agent_switcher, switch_to_agent_tool, 
#     return_to_iriska_tool, get_current_agent_tool
# )
# from agent.memory import add_message
# from agent.retriever import get_relevant_documents

logger = logging.getLogger(__name__)

# Основной роутер для чата
router = APIRouter()

# OpenAI совместимый роутер
openai_router = APIRouter()

@openai_router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Основной endpoint для чата с агентами (OpenAI совместимый).
    
    Поддерживает:
    - Чат с Ириской (главным агентом)
    - Переключение на специализированных агентов
    - Сохранение контекста разговора
    """
    try:
        logger.info(f"💬 Чат запрос получен: model={request.model}, messages_count={len(request.messages)}")
        logger.info(f"💬 Последнее сообщение: {request.messages[-1].content[:100]}...")
        logger.info(f"💬 Структура запроса: {request.dict()}")
        
        # Валидация входящих данных
        if not request.messages:
            logger.error("❌ Пустой список сообщений")
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        if not request.model:
            logger.error("❌ Не указана модель")
            raise HTTPException(status_code=400, detail="Model is required")
        
        # TODO: Реализовать получение текущего агента
        current_agent = "Ириска"
        logger.info(f"🤖 Текущий агент: {current_agent}")
        
        # Обрабатываем специальные команды для переключения агентов
        user_message = request.messages[-1].content.lower()
        
        # Команды переключения на специализированных агентов
        if any(phrase in user_message for phrase in [
            "переключись на", "активируй", "запусти агента", "включи"
        ]):
            # Извлекаем имя агента из сообщения
            agent_name = None
            for phrase in ["переключись на", "активируй", "запусти агента", "включи"]:
                if phrase in user_message:
                    parts = user_message.split(phrase)
                    if len(parts) > 1:
                        agent_name = parts[1].strip().split()[0]
                        break
            
            if agent_name:
                # TODO: Реализовать переключение на агента
                switch_result = f"✅ Переключение на агента {agent_name} выполнено"
                return ChatResponse(
                    id=f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    object="chat.completion",
                    choices=[{
                        "message": Message(
                            role="assistant",
                            content=switch_result
                        ),
                        "finish_reason": "stop"
                    }],
                    usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
                )
        
        # Команды возврата к Ириске
        elif any(phrase in user_message for phrase in [
            "вернись к себе", "вернись к ириске", "вернись", "ириска"
        ]):
            # TODO: Реализовать возврат к Ириске
            return_result = "✅ Возврат к Ириске выполнен"
            return ChatResponse(
                id=f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                object="chat.completion",
                choices=[{
                    "message": Message(
                        role="assistant",
                        content=return_result
                    ),
                    "finish_reason": "stop"
                }],
                usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
            )
        
        # Команды получения информации о текущем агенте
        elif any(phrase in user_message for phrase in [
            "кто ты", "кто ты такой", "представься", "статус"
        ]):
            # TODO: Реализовать получение информации об агенте
            agent_info = f"Я {current_agent} - твой AI помощник!"
            return ChatResponse(
                id=f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                object="chat.completion",
                choices=[{
                    "message": Message(
                        role="assistant",
                        content=agent_info
                    ),
                    "finish_reason": "stop"
                }],
                usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
            )
        
        # Обычный чат - обрабатываем через LLM
        else:
            # TODO: Реализовать получение контекста из памяти
            context = None
            
            # Формируем ответ в зависимости от текущего агента
            if current_agent == "Ириска":
                response_content = f"Привет, Марат! Я Ириска - твой главный AI-менеджер! 🚀\n\nТы спросил: '{request.messages[-1].content}'\n\nЯ могу:\n• Помочь с любыми задачами\n• Создать нового специализированного агента\n• Переключить тебя на другого агента\n• Показать статус системы\n\nЧто хочешь сделать?"
            else:
                response_content = f"Привет! Я {current_agent} - специализированный агент.\n\nТы спросил: '{request.messages[-1].content}'\n\nЯ готов помочь в рамках своей специализации! Если нужна помощь с чем-то другим, скажи 'Вернись к Ириске'."
            
            # TODO: Реализовать сохранение сообщений в память
            # add_message(
            #     message=request.messages[-1].content,
            #     role="user",
            #     emotion="neutral"
            # )
            # add_message(
            #     message=response_content,
            #     role="assistant",
            #     emotion="friendly"
            # )
            
            return ChatResponse(
                id=f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                object="chat.completion",
                choices=[{
                    "message": Message(
                        role="assistant",
                        content=response_content
                    ),
                    "finish_reason": "stop"
                }],
                usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка в чате: {e}")
        error_response = f"Извини, Марат! У меня проблемы с обработкой запроса. Попробуй еще раз или скажи 'Вернись к Ириске' для сброса."
        
        return ChatResponse(
            id=f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            object="chat.completion",
            choices=[{
                "message": Message(
                    role="assistant",
                    content=error_response
                ),
                "finish_reason": "stop"
            }],
            usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
        )

# Внутренние API роуты для чата
@router.get("/status")
async def get_chat_status():
    """Получает статус чата"""
    return {
        "status": "active",
        "current_agent": "Ириска",  # TODO: Реализовать получение текущего агента
        "timestamp": datetime.utcnow().isoformat()
    }
