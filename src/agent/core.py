import json
import logging
from typing import Dict, List, Any
from schemas.openai import ChatRequest, ChatResponse
from agent.memory import memory, working_memory
from agent.retriever import retriever
from agent.models import SessionLocal
from tools.profile_switcher import detect_profile_switch, get_profile_by_name
from agent.profile_manager import active_profiles, get_agent_profile
from agent.llm_client import llama_cpp_completion
from agent.emotions import analyze_emotion
from agent.retriever import save_summary_to_chroma
from agent.prompt_builder import PromptBuilder, PromptComponents
from agent.emotional_memory import get_emotional_integration

# TODO (core):
# - Поддержка streaming-ответов (SSE/WebSocket) на уровне агента
# - Обработка вложений (attachments): извлечение текста и безопасная передача в промпт
# - Интеграция RAG: приоритет локальных эмбеддингов, fallback, конфигурируемость
# - Улучшить управление профилями: явное переключение, приоритеты, audit trail в БД
# - Улучшить промптинг: шаблоны, системные инструкции, контроль длины срезов истории
# - Метрики/трейсинг: время ответа, токены, причины обрезки, ошибки LLM
# - Улучшить обработку ошибок и таймаутов, ретраи к LLM серверу
# - Развести пути БД: отдельный URL для SQLAlchemy и файл для LangChain memory
# - Оптимизировать сохранение в память: лимиты, очистка, приватность
# - Тесты: юнит-тесты на ветвление профилей/эмоций/контекст

logger = logging.getLogger(__name__)

# Инициализируем PromptBuilder для сборки промптов
prompt_builder = PromptBuilder()

async def agent_respond(request: ChatRequest) -> ChatResponse:
    """
    Основная функция ответа агента с использованием структурированного промпта.
    
    Процесс:
    1. Определение/переключение профиля пользователя
    2. Сборка контекста и истории
    3. Анализ эмоций пользователя
    4. Сборка структурированного промпта через PromptBuilder
    5. Генерация ответа с параметрами профиля
    6. Сохранение в память и логирование
    """
    try:
        user_id = request.user or "default"
        last_message = request.messages[-1].content
        
        # Шаг 1: Определение профиля пользователя
        profile = await _get_user_profile(user_id, last_message)
        if not profile:
            logger.error(f"Не удалось получить профиль для пользователя {user_id}")
            return _create_error_response("Ошибка инициализации профиля")
        
        # Шаг 2: Сборка контекста и истории
        context, conversation_history = await _build_context_and_history(request.messages)
        
        # Шаг 3: Обработка через эмоциональную память (если доступна)
        emotional_context_data = {}
        emotional_integration = get_emotional_integration()
        if emotional_integration:
            try:
                conversation_context = [msg.content for msg in request.messages[:-1]]
                emotional_result = await emotional_integration.process_user_message(
                    last_message, user_id, conversation_context
                )
                emotional_context_data = emotional_result.get("emotional_context", {})
                logger.info(f"Эмоциональный контекст: {emotional_context_data.get('user_emotion', {}).get('type', 'unknown')}")
            except Exception as e:
                logger.warning(f"Ошибка обработки эмоциональной памяти: {e}")
        
        # Шаг 3 (fallback): Базовый анализ эмоций
        emotion = analyze_emotion(last_message)
        logger.info(f"Базовая эмоция пользователя: {emotion}")
        
        # Шаг 4: Сборка структурированного промпта с эмоциональным контекстом
        emotional_context_text = ""
        if emotional_integration:
            emotional_context_text = emotional_integration.get_emotional_context_for_prompt(last_message, user_id)
        
        prompt = await _build_structured_prompt(profile, last_message, context, conversation_history, emotional_context_text)
        
        # Шаг 5: Генерация ответа с параметрами профиля
        llm_response = await _generate_response_with_profile(profile, prompt)
        
        # Шаг 6: Сохранение в память и обновление рабочей памяти
        await _update_memory_and_context(last_message, llm_response, emotion)
        
        # Шаг 7: Формирование финального ответа
        response_text = _format_response_with_profile(profile, llm_response)
        
        return ChatResponse(
            id="chatcmpl-001",
            object="chat.completion",
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": response_text.strip()},
                "finish_reason": "stop"
            }],
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        )
        
    except Exception as e:
        logger.exception(f"Ошибка в agent_respond: {e}")
        raise

async def _get_user_profile(user_id: str, last_message: str) -> 'AgentProfile':
    """
    Получение профиля пользователя с возможностью переключения.
    
    Args:
        user_id: ID пользователя
        last_message: Последнее сообщение пользователя
        
    Returns:
        Профиль агента для пользователя
    """
    try:
        # Проверяем, хочет ли пользователь сменить профиль
        profile_name = detect_profile_switch(last_message)
        if profile_name:
            profile = get_profile_by_name(profile_name)
            if profile:
                active_profiles.set(user_id, profile)
                logger.info(f"Пользователь {user_id} переключился на профиль: {profile_name}")
            else:
                logger.warning(f"Профиль {profile_name} не найден для пользователя {user_id}")
        
        # Получаем активный профиль
        profile = active_profiles.get(user_id)
        if not profile:
            # Если профиль не найден, получаем дефолтный из БД
            with SessionLocal() as session:
                profile = get_agent_profile(session, agent_id=1)
            if profile:
                active_profiles.set(user_id, profile)
                logger.info(f"Установлен дефолтный профиль для пользователя {user_id}")
            else:
                logger.error(f"Не удалось получить дефолтный профиль для пользователя {user_id}")
                return None
        
        return profile
        
    except Exception as e:
        logger.exception(f"Ошибка получения профиля пользователя {user_id}: {e}")
        return None

async def _build_context_and_history(messages: list) -> tuple[str, str]:
    """
    Сборка контекста и истории диалога.
    
    Args:
        messages: История сообщений
        
    Returns:
        Кортеж (context, conversation_history)
    """
    context = ""
    conversation_history = ""
    
    try:
        # Получаем контекст из ChromaDB (если доступен)
        if retriever:
            try:
                last_user_message = messages[-1].content if messages else ""
                
                # Используем улучшенный ретривер если доступен
                try:
                    from agent.memory.enhanced_retriever import EnhancedRetriever
                    from agent.memory.config_loader import get_agent_summarization_config
                    
                    # Получаем конфигурацию для агента
                    agent_name = profile.name if profile else "default"
                    config = get_agent_summarization_config(agent_name)
                    
                    enhanced_retriever = EnhancedRetriever(retriever, config=config)
                    context, context_docs = await enhanced_retriever.get_relevant_context(
                        last_user_message, user_id=user_id, k=config.get("final_k", 4)
                    )
                    logger.debug(f"Enhanced retrieval: {len(context)} chars from {len(context_docs)} docs")
                except ImportError:
                    # Fallback на базовый ретривер
                    context_docs = retriever.get_relevant_documents(last_user_message)
                    context = "\n".join([doc.page_content for doc in context_docs]) if context_docs else ""
                    logger.debug(f"Basic retrieval: {len(context)} chars")
                    
            except Exception as e:
                logger.error(f"Ошибка получения контекста из ChromaDB: {e}")
                context = ""
        
        # Собираем историю диалога (последние 5 сообщений)
        if len(messages) > 1:
            history_messages = messages[-6:-1]  # Исключаем последнее сообщение
            conversation_history = "\n".join([
                f"{msg.role}: {msg.content}" for msg in history_messages
            ])
        
        return context, conversation_history
        
    except Exception as e:
        logger.error(f"Ошибка сборки контекста и истории: {e}")
        return "", ""

async def _build_structured_prompt(profile: 'AgentProfile', user_message: str, context: str, conversation_history: str, emotional_context: str = "") -> str:
    """
    Сборка структурированного промпта через PromptBuilder.
    
    Args:
        profile: Профиль агента
        user_message: Сообщение пользователя
        context: Контекст из RAG
        conversation_history: История диалога
        
    Returns:
        Структурированный промпт
    """
    try:
        # Создаём компоненты для промпта
        # Добавляем эмоциональный контекст к обычному контексту
        full_context = context
        if emotional_context:
            full_context = f"{context}\n\n{emotional_context}" if context else emotional_context
        
        components = PromptComponents(
            system_prompt=profile.system_prompt or "",
            persona_traits=profile.persona_traits or "",
            safety_rules=profile.safety_rules or "",
            context=full_context,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        # Собираем промпт через PromptBuilder
        prompt = prompt_builder.build_prompt(profile, components)
        
        logger.debug(f"Промпт собран: {len(prompt)} символов")
        return prompt
        
    except Exception as e:
        logger.error(f"Ошибка сборки структурированного промпта: {e}")
        # Fallback на простой промпт
        return f"[User]\n{user_message}\n\n[Assistant]\n"

async def _generate_response_with_profile(profile: 'AgentProfile', prompt: str) -> str:
    """
    Генерация ответа с использованием параметров профиля.
    
    Args:
        profile: Профиль агента
        prompt: Собранный промпт
        
    Returns:
        Ответ от LLM
    """
    try:
        # Получаем параметры генерации из профиля
        gen_settings = prompt_builder.get_generation_settings(profile)
        
        # Генерируем ответ с параметрами профиля
        llm_response = await llama_cpp_completion(prompt)
        
        logger.debug(f"Ответ сгенерирован с параметрами: {gen_settings}")
        return llm_response
        
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        return "[Ошибка генерации ответа]"

async def _update_memory_and_context(user_message: str, llm_response: str, emotion: str):
    """
    Обновление памяти и контекста.
    
    Args:
        user_message: Сообщение пользователя
        llm_response: Ответ LLM
        emotion: Эмоция пользователя
    """
    try:
        # Сохраняем в диалоговую память
        if memory:
            memory.save_context({"input": user_message}, {"output": llm_response})
        
        # Добавляем в рабочую память
        working_memory.add_message(user_message, emotion=emotion)
        
        # Сохраняем summary в ChromaDB
        save_summary_to_chroma()
        
    except Exception as e:
        logger.error(f"Ошибка обновления памяти: {e}")

def _format_response_with_profile(profile: 'AgentProfile', llm_response: str) -> str:
    """
    Форматирование ответа с учётом профиля.
    
    Args:
        profile: Профиль агента
        llm_response: Ответ от LLM
        
    Returns:
        Отформатированный ответ
    """
    try:
        # Базовый ответ
        response_parts = [llm_response.strip()]
        
        # Добавляем подпись и эмодзи
        if profile.signature:
            response_parts.append(profile.signature)
        if profile.emoji:
            response_parts.append(profile.emoji)
        
        return " ".join(response_parts)
        
    except Exception as e:
        logger.error(f"Ошибка форматирования ответа: {e}")
        return llm_response.strip()

def _create_error_response(error_message: str) -> ChatResponse:
    """
    Создание ответа с ошибкой.
    
    Args:
        error_message: Сообщение об ошибке
        
    Returns:
        ChatResponse с ошибкой
    """
    return ChatResponse(
        id="chatcmpl-error",
        object="chat.completion",
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": f"Извините, произошла ошибка: {error_message}"},
            "finish_reason": "error"
        }],
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


async def process_user_feedback(user_id: str, feedback_text: str, conversation_context: List[str] = None) -> Dict[str, Any]:
    """
    Обрабатывает обратную связь пользователя и корректирует профиль агента
    
    Args:
        user_id: ID пользователя
        feedback_text: Текст обратной связи
        conversation_context: Контекст разговора
        
    Returns:
        Результат обработки обратной связи
    """
    try:
        emotional_integration = get_emotional_integration()
        if not emotional_integration:
            logger.warning("Эмоциональная память не инициализирована")
            return {"status": "emotional_memory_not_available"}
        
        result = await emotional_integration.process_feedback(
            user_id, feedback_text, conversation_context
        )
        
        logger.info(f"Обработана обратная связь от {user_id}: {result.get('status', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка обработки обратной связи: {e}")
        return {"status": "error", "error": str(e)} 