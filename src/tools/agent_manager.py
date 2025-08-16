"""
Tools для управления множественными агентами.
Ириска использует эти tools для создания, активации и контроля подчиненных агентов.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Импортируем модели для работы с БД
from agent.models import (
    SessionLocal, AgentProfile, AgentActivity, AgentContext,
    get_agent_profile_by_name, get_all_active_agents, get_agent_templates,
    update_agent_status
)

logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC МОДЕЛИ ДЛЯ ВАЛИДАЦИИ ДАННЫХ
# ============================================================================

class CreateAgentRequest(BaseModel):
    """Запрос на создание нового агента"""
    name: str = Field(..., description="Уникальное имя агента")
    specialization: str = Field(..., description="Специализация агента (аналитика, креатив, помощь)")
    purpose: str = Field(..., description="Описание назначения агента")
    system_prompt: str = Field(..., description="Основная инструкция для LLM")
    personality_traits: List[str] = Field(default=[], description="Черты характера")
    tone: str = Field(default="friendly", description="Тон общения")
    communication_style: str = Field(default="", description="Стиль общения")
    safety_rules: str = Field(default="", description="Правила безопасности")
    allowed_tools: List[str] = Field(default=[], description="Разрешенные tools")
    restricted_actions: str = Field(default="", description="Запрещенные действия")
    max_tokens: int = Field(default=1000, description="Максимум токенов")
    temperature: str = Field(default="0.7", description="Температура (креативность)")
    tags: List[str] = Field(default=[], description="Теги для категоризации")
    description: str = Field(default="", description="Описание агента")
    notes: str = Field(default="", description="Заметки и комментарии")

class AgentStatusResponse(BaseModel):
    """Ответ с информацией о статусе агента"""
    name: str
    status: str
    current_user_id: Optional[str]
    last_activated: Optional[str]
    messages_processed: int
    tokens_used: int
    current_context: Optional[str]
    last_error: Optional[str]

class AgentListResponse(BaseModel):
    """Ответ со списком агентов"""
    agents: List[Dict[str, Any]]
    total_count: int
    active_count: int
    template_count: int

# ============================================================================
# TOOLS ДЛЯ УПРАВЛЕНИЯ АГЕНТАМИ
# ============================================================================

def create_agent_profile(
    name: str,
    specialization: str,
    purpose: str,
    system_prompt: str,
    personality_traits: Optional[List[str]] = None,
    tone: str = "friendly",
    communication_style: str = "",
    safety_rules: str = "",
    allowed_tools: Optional[List[str]] = None,
    restricted_actions: str = "",
    max_tokens: int = 1000,
    temperature: str = "0.7",
    tags: Optional[List[str]] = None,
    description: str = "",
    notes: str = ""
) -> str:
    """
    Создает новый профиль специализированного агента.
    
    Этот tool позволяет Ириске создавать новых агентов для конкретных задач.
    Каждый агент имеет ограниченные права доступа и специализацию.
    
    Args:
        name: Уникальное имя агента
        specialization: Специализация (аналитика, креатив, помощь)
        purpose: Описание назначения
        system_prompt: Основная инструкция для LLM
        personality_traits: Черты характера
        tone: Тон общения
        communication_style: Стиль общения
        safety_rules: Правила безопасности
        allowed_tools: Разрешенные tools
        restricted_actions: Запрещенные действия
        max_tokens: Максимум токенов
        temperature: Температура (креативность)
        tags: Теги для категоризации
        description: Описание агента
        notes: Заметки
        
    Returns:
        str: Сообщение о результате создания
        
    Example:
        create_agent_profile(
            name="DataAnalyst",
            specialization="Анализ данных",
            purpose="Специалист по анализу данных и статистике",
            system_prompt="Ты аналитик данных...",
            personality_traits=["логичный", "точный"],
            allowed_tools=["data_analysis", "statistics"]
        )
    """
    try:
        # Проверяем, не существует ли уже агент с таким именем
        existing_agent = get_agent_profile_by_name(name)
        if existing_agent:
            return f"❌ Агент с именем '{name}' уже существует!"
        
        # Подготавливаем данные
        if personality_traits is None:
            personality_traits = []
        if allowed_tools is None:
            allowed_tools = []
        if tags is None:
            tags = []
        
        # Создаем новый профиль агента
        new_agent = AgentProfile(
            name=name,
            created_by="Ириска",  # Ириска создает всех агентов
            status="active",  # По умолчанию активен
            access_level="restricted",  # Ограниченные права
            is_main_agent=False,  # Не главный агент
            specialization=specialization,
            purpose=purpose,
            system_prompt=system_prompt,
            personality_traits=json.dumps(personality_traits, ensure_ascii=False),
            tone=tone,
            communication_style=communication_style,
            safety_rules=safety_rules,
            allowed_tools=json.dumps(allowed_tools, ensure_ascii=False),
            restricted_actions=restricted_actions,
            generation_settings=json.dumps({
                "model": "default",
                "max_tokens": max_tokens,
                "temperature": temperature
            }, ensure_ascii=False),
            max_tokens=max_tokens,
            temperature=temperature,
            version="1.0.0",
            is_template=False,
            tags=json.dumps(tags, ensure_ascii=False),
            description=description,
            notes=notes
        )
        
        # Сохраняем в БД
        with SessionLocal() as session:
            session.add(new_agent)
            session.commit()
            
            # Создаем запись активности для нового агента
            activity = AgentActivity(
                agent_name=name,
                current_status="inactive",  # Пока не активирован
                last_heartbeat=datetime.utcnow()
            )
            session.add(activity)
            session.commit()
        
        logger.info(f"✅ Создан новый агент: {name} ({specialization})")
        return f"🎉 Агент '{name}' успешно создан!\n\n📋 Специализация: {specialization}\n🎯 Назначение: {purpose}\n🔒 Права: ограниченные\n📊 Статус: активен"
        
    except Exception as e:
        error_msg = f"❌ Ошибка создания агента '{name}': {str(e)}"
        logger.error(error_msg)
        return error_msg

def activate_agent(agent_name: str, user_id: str = "default") -> str:
    """
    Активирует указанного агента для работы с пользователем.
    
    При активации агента:
    - Сохраняется контекст текущего агента (если есть)
    - Активируется новый агент
    - Обновляется статистика использования
    
    Args:
        agent_name: Имя агента для активации
        user_id: ID пользователя
        
    Returns:
        str: Сообщение о результате активации
        
    Example:
        activate_agent("DataAnalyst", "user123")
    """
    try:
        # Проверяем существование агента
        agent = get_agent_profile_by_name(agent_name)
        if not agent:
            return f"❌ Агент '{agent_name}' не найден!"
        
        # Проверяем статус агента
        if agent.status != "active":
            return f"❌ Агент '{agent_name}' неактивен (статус: {agent.status})"
        
        with SessionLocal() as session:
            # Получаем или создаем запись активности
            activity = session.query(AgentActivity).filter_by(agent_name=agent_name).first()
            if not activity:
                activity = AgentActivity(agent_name=agent_name)
                session.add(activity)
            
            # Активируем агента
            activity.current_status = "active"
            activity.current_user_id = user_id
            activity.activated_at = datetime.utcnow()
            activity.session_start = datetime.utcnow()
            activity.last_heartbeat = datetime.utcnow()
            
            # Обновляем профиль агента
            agent.last_activated = datetime.utcnow()
            agent.usage_count += 1
            
            session.commit()
        
        logger.info(f"✅ Агент '{agent_name}' активирован для пользователя {user_id}")
        return f"🚀 Агент '{agent_name}' активирован!\n\n📋 Специализация: {agent.specialization}\n🎯 Назначение: {agent.purpose}\n👤 Пользователь: {user_id}"
        
    except Exception as e:
        error_msg = f"❌ Ошибка активации агента '{agent_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg

def deactivate_agent(agent_name: str) -> str:
    """
    Деактивирует указанного агента.
    
    При деактивации:
    - Сохраняется контекст работы
    - Обновляется статистика
    - Агент переходит в неактивное состояние
    
    Args:
        agent_name: Имя агента для деактивации
        
    Returns:
        str: Сообщение о результате деактивации
    """
    try:
        with SessionLocal() as session:
            # Получаем активность агента
            activity = session.query(AgentActivity).filter_by(agent_name=agent_name).first()
            if not activity:
                return f"❌ Активность агента '{agent_name}' не найдена!"
            
            if activity.current_status != "active":
                return f"❌ Агент '{agent_name}' уже неактивен (статус: {activity.current_status})"
            
            # Деактивируем агента
            activity.current_status = "inactive"
            activity.deactivated_at = datetime.utcnow()
            activity.current_user_id = None
            
            # Сохраняем статистику сессии
            if activity.session_start:
                session_duration = datetime.utcnow() - activity.session_start
                logger.info(f"Сессия агента '{agent_name}' длилась: {session_duration}")
            
            session.commit()
        
        logger.info(f"✅ Агент '{agent_name}' деактивирован")
        return f"⏸️ Агент '{agent_name}' деактивирован\n\n📊 Обработано сообщений: {activity.messages_processed}\n🔢 Использовано токенов: {activity.tokens_used}"
        
    except Exception as e:
        error_msg = f"❌ Ошибка деактивации агента '{agent_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg

def list_active_agents() -> str:
    """
    Показывает список всех активных агентов в системе.
    
    Returns:
        str: Форматированный список агентов с их статусами
    """
    try:
        # Получаем всех активных агентов
        active_agents = get_all_active_agents()
        
        if not active_agents:
            return "📋 В системе нет активных агентов"
        
        # Формируем список
        result = "📋 **Активные агенты в системе:**\n\n"
        
        for agent in active_agents:
            # Получаем текущую активность
            with SessionLocal() as session:
                activity = session.query(AgentActivity).filter_by(agent_name=agent.name).first()
                status = activity.current_status if activity else "неизвестно"
                user_id = activity.current_user_id if activity else "нет"
            
            # Определяем эмодзи для типа агента
            if agent.is_main_agent:
                emoji = "👑"  # Главный агент
            elif agent.specialization and "анализ" in agent.specialization.lower():
                emoji = "📊"  # Аналитик
            elif agent.specialization and "креатив" in agent.specialization.lower():
                emoji = "🎨"  # Креативщик
            else:
                emoji = "🤖"  # Обычный агент
            
            result += f"{emoji} **{agent.name}**\n"
            result += f"   📋 Специализация: {agent.specialization or 'не указана'}\n"
            result += f"   🔒 Права: {agent.access_level}\n"
            result += f"   📊 Статус: {status}\n"
            result += f"   👤 Пользователь: {user_id or 'нет'}\n"
            result += f"   📈 Использований: {agent.usage_count}\n\n"
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Ошибка получения списка агентов: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_agent_status(agent_name: str) -> str:
    """
    Получает детальную информацию о статусе конкретного агента.
    
    Args:
        agent_name: Имя агента
        
    Returns:
        str: Детальная информация о статусе
    """
    try:
        # Получаем профиль агента
        agent = get_agent_profile_by_name(agent_name)
        if not agent:
            return f"❌ Агент '{agent_name}' не найден!"
        
        with SessionLocal() as session:
            # Получаем активность агента
            activity = session.query(AgentActivity).filter_by(agent_name=agent_name).first()
            
            result = f"📊 **Статус агента '{agent_name}'**\n\n"
            result += f"📋 **Основная информация:**\n"
            result += f"   🎯 Специализация: {agent.specialization or 'не указана'}\n"
            result += f"   🔒 Права доступа: {agent.access_level}\n"
            result += f"   📊 Статус профиля: {agent.status}\n"
            result += f"   👑 Главный агент: {'Да' if agent.is_main_agent else 'Нет'}\n"
            result += f"   📅 Создан: {agent.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            result += f"   📈 Всего использований: {agent.usage_count}\n"
            result += f"   🔢 Всего токенов: {agent.total_tokens_used}\n\n"
            
            if activity:
                result += f"📊 **Текущая активность:**\n"
                result += f"   📊 Статус: {activity.current_status}\n"
                result += f"   👤 Пользователь: {activity.current_user_id or 'нет'}\n"
                result += f"   🚀 Активирован: {activity.activated_at.strftime('%Y-%m-%d %H:%M') if activity.activated_at else 'нет'}\n"
                result += f"   💬 Сообщений в сессии: {activity.messages_processed}\n"
                result += f"   🔢 Токенов в сессии: {activity.tokens_used}\n"
                result += f"   ❌ Ошибок: {activity.error_count}\n"
                
                if activity.last_error:
                    result += f"   ⚠️ Последняя ошибка: {activity.last_error}\n"
            else:
                result += f"📊 **Активность:** Нет данных об активности\n"
            
            result += f"\n🎭 **Личность:**\n"
            result += f"   🎨 Тон: {agent.tone}\n"
            result += f"   💬 Стиль: {agent.communication_style or 'не указан'}\n"
            result += f"   🔢 Макс. токенов: {agent.max_tokens}\n"
            result += f"   🌡️ Температура: {agent.temperature}\n"
            
            return result
            
    except Exception as e:
        error_msg = f"❌ Ошибка получения статуса агента '{agent_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg

def monitor_agent_activity() -> str:
    """
    Мониторит активность всех агентов в системе.
    
    Returns:
        str: Отчет об активности агентов
    """
    try:
        with SessionLocal() as session:
            # Получаем все записи активности
            activities = session.query(AgentActivity).all()
            
            if not activities:
                return "📊 Нет данных об активности агентов"
            
            result = "📊 **Мониторинг активности агентов**\n\n"
            
            # Группируем по статусам
            status_counts = {}
            for activity in activities:
                status = activity.current_status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            result += f"📈 **Статистика по статусам:**\n"
            for status, count in status_counts.items():
                emoji = {
                    "active": "🟢",
                    "inactive": "⚪",
                    "busy": "🟡",
                    "error": "🔴"
                }.get(status, "❓")
                result += f"   {emoji} {status}: {count}\n"
            
            result += f"\n📋 **Детальная информация:**\n"
            
            for activity in activities:
                # Получаем профиль агента
                agent = session.query(AgentProfile).filter_by(name=activity.agent_name).first()
                if not agent:
                    continue
                
                # Определяем эмодзи для статуса
                status_emoji = {
                    "active": "🟢",
                    "inactive": "⚪",
                    "busy": "🟡",
                    "error": "🔴"
                }.get(activity.current_status, "❓")
                
                result += f"\n{status_emoji} **{activity.agent_name}**\n"
                result += f"   📊 Статус: {activity.current_status}\n"
                result += f"   👤 Пользователь: {activity.current_user_id or 'нет'}\n"
                result += f"   💬 Сообщений: {activity.messages_processed}\n"
                result += f"   🔢 Токенов: {activity.tokens_used}\n"
                result += f"   ❌ Ошибок: {activity.error_count}\n"
                
                if activity.last_heartbeat:
                    time_diff = datetime.utcnow() - activity.last_heartbeat
                    result += f"   ⏰ Последний сигнал: {time_diff.total_seconds():.0f} сек назад\n"
            
            return result
            
    except Exception as e:
        error_msg = f"❌ Ошибка мониторинга активности: {str(e)}"
        logger.error(error_msg)
        return error_msg

def create_agent_from_template(template_name: str, new_name: str, customization: str = "") -> str:
    """
    Создает нового агента на основе существующего шаблона.
    
    Args:
        template_name: Имя шаблона для копирования
        new_name: Новое имя для агента
        customization: Дополнительные настройки
        
    Returns:
        str: Результат создания агента
    """
    try:
        # Получаем шаблон
        template = get_agent_profile_by_name(template_name)
        if not template:
            return f"❌ Шаблон '{template_name}' не найден!"
        
        if not template.is_template:
            return f"❌ '{template_name}' не является шаблоном!"
        
        # Проверяем, не существует ли уже агент с новым именем
        existing_agent = get_agent_profile_by_name(new_name)
        if existing_agent:
            return f"❌ Агент с именем '{new_name}' уже существует!"
        
        # Создаем нового агента на основе шаблона
        new_agent = AgentProfile(
            name=new_name,
            created_by="Ириска",
            status="active",
            access_level=template.access_level,
            is_main_agent=False,
            specialization=template.specialization,
            purpose=template.purpose,
            system_prompt=template.system_prompt,
            personality_traits=template.personality_traits,
            tone=template.tone,
            communication_style=template.communication_style,
            safety_rules=template.safety_rules,
            allowed_tools=template.allowed_tools,
            restricted_actions=template.restricted_actions,
            generation_settings=template.generation_settings,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            version="1.0.0",
            is_template=False,
            tags=template.tags,
            description=f"Создан на основе шаблона '{template_name}'",
            notes=f"Кастомизация: {customization}" if customization else f"Создан на основе шаблона '{template_name}'"
        )
        
        # Сохраняем в БД
        with SessionLocal() as session:
            session.add(new_agent)
            session.commit()
            
            # Создаем запись активности
            activity = AgentActivity(
                agent_name=new_name,
                current_status="inactive",
                last_heartbeat=datetime.utcnow()
            )
            session.add(activity)
            session.commit()
        
        logger.info(f"✅ Создан агент '{new_name}' на основе шаблона '{template_name}'")
        return f"🎉 Агент '{new_name}' создан на основе шаблона '{template_name}'!\n\n📋 Специализация: {template.specialization}\n🎯 Назначение: {template.purpose}\n🔒 Права: {template.access_level}\n📊 Статус: активен"
        
    except Exception as e:
        error_msg = f"❌ Ошибка создания агента из шаблона: {str(e)}"
        logger.error(error_msg)
        return error_msg

# ============================================================================
# СПИСОК ВСЕХ TOOLS ДЛЯ ИРИСКИ
# ============================================================================

AGENT_MANAGEMENT_TOOLS = {
    "create_agent_profile": {
        "function": create_agent_profile,
        "description": "Создает новый профиль специализированного агента",
        "parameters": {
            "name": "Уникальное имя агента",
            "specialization": "Специализация (аналитика, креатив, помощь)",
            "purpose": "Описание назначения",
            "system_prompt": "Основная инструкция для LLM",
            "personality_traits": "Черты характера (список)",
            "tone": "Тон общения (friendly, professional, creative)",
            "communication_style": "Стиль общения",
            "safety_rules": "Правила безопасности",
            "allowed_tools": "Разрешенные tools (список)",
            "restricted_actions": "Запрещенные действия",
            "max_tokens": "Максимум токенов",
            "temperature": "Температура (креативность)",
            "tags": "Теги для категоризации",
            "description": "Описание агента",
            "notes": "Заметки и комментарии"
        }
    },
    "activate_agent": {
        "function": activate_agent,
        "description": "Активирует указанного агента для работы с пользователем",
        "parameters": {
            "agent_name": "Имя агента для активации",
            "user_id": "ID пользователя (опционально)"
        }
    },
    "deactivate_agent": {
        "function": deactivate_agent,
        "description": "Деактивирует указанного агента",
        "parameters": {
            "agent_name": "Имя агента для деактивации"
        }
    },
    "list_active_agents": {
        "function": list_active_agents,
        "description": "Показывает список всех активных агентов в системе",
        "parameters": {}
    },
    "get_agent_status": {
        "function": get_agent_status,
        "description": "Получает детальную информацию о статусе конкретного агента",
        "parameters": {
            "agent_name": "Имя агента"
        }
    },
    "monitor_agent_activity": {
        "function": monitor_agent_activity,
        "description": "Мониторит активность всех агентов в системе",
        "parameters": {}
    },
    "create_agent_from_template": {
        "function": create_agent_from_template,
        "description": "Создает нового агента на основе существующего шаблона",
        "parameters": {
            "template_name": "Имя шаблона для копирования",
            "new_name": "Новое имя для агента",
            "customization": "Дополнительные настройки (опционально)"
        }
    }
}

# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С TOOLS
# ============================================================================

def get_tool_by_name(tool_name: str):
    """
    Получает tool по имени.
    
    Args:
        tool_name: Имя tool
        
    Returns:
        dict: Информация о tool или None
    """
    return AGENT_MANAGEMENT_TOOLS.get(tool_name)

def get_all_tools_info() -> Dict[str, Dict]:
    """
    Получает информацию о всех доступных tools.
    
    Returns:
        Dict: Словарь с информацией о всех tools
    """
    return AGENT_MANAGEMENT_TOOLS

def execute_tool(tool_name: str, **kwargs) -> str:
    """
    Выполняет указанный tool с переданными параметрами.
    
    Args:
        tool_name: Имя tool для выполнения
        **kwargs: Параметры для tool
        
    Returns:
        str: Результат выполнения tool
    """
    try:
        tool_info = get_tool_by_name(tool_name)
        if not tool_info:
            return f"❌ Tool '{tool_name}' не найден!"
        
        # Выполняем tool
        result = tool_info["function"](**kwargs)
        return result
        
    except Exception as e:
        error_msg = f"❌ Ошибка выполнения tool '{tool_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg

# ============================================================================
# ТЕСТИРОВАНИЕ TOOLS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Тестирование tools управления агентами...")
    
    # Тест создания агента
    print("\n1. Тест создания агента:")
    result = create_agent_profile(
        name="TestAnalyst",
        specialization="Тестовая аналитика",
        purpose="Тестовый агент для проверки функциональности",
        system_prompt="Ты тестовый аналитик",
        personality_traits=["тестовый", "аналитический"],
        allowed_tools=["test_tool"]
    )
    print(result)
    
    # Тест списка агентов
    print("\n2. Тест списка агентов:")
    result = list_active_agents()
    print(result)
    
    # Тест статуса агента
    print("\n3. Тест статуса агента:")
    result = get_agent_status("TestAnalyst")
    print(result)
    
    print("\n✅ Тестирование завершено!")
