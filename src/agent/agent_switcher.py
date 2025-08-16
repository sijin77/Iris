"""
Система переключения между агентами.
Позволяет Ириске переключаться на специализированных агентов и возвращаться к себе.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

# Импортируем модели и tools
from agent.models import (
    SessionLocal, AgentProfile, AgentActivity, AgentContext,
    get_agent_profile_by_name, get_all_active_agents
)
from tools.agent_manager import (
    activate_agent, deactivate_agent, get_agent_status
)

logger = logging.getLogger(__name__)

# ============================================================================
# КЛАСС МЕНЕДЖЕРА ПЕРЕКЛЮЧЕНИЯ АГЕНТОВ
# ============================================================================

class AgentSwitcher:
    """
    Менеджер для переключения между агентами.
    
    Основные функции:
    - Переключение на специализированного агента
    - Возврат к Ириске (главному агенту)
    - Сохранение и восстановление контекста
    - Управление жизненным циклом агентов
    """
    
    def __init__(self):
        """Инициализация менеджера переключения"""
        self.current_agent = "Ириска"  # По умолчанию активна Ириска
        self.previous_agent = None  # Предыдущий агент для возврата
        self.switch_history = []  # История переключений
        self.context_cache = {}  # Кэш контекстов агентов
        
        logger.info("🚀 AgentSwitcher инициализирован")
    
    def get_current_agent(self) -> str:
        """
        Получает имя текущего активного агента.
        
        Returns:
            str: Имя текущего агента
        """
        return self.current_agent
    
    def is_iriska_active(self) -> bool:
        """
        Проверяет, активна ли Ириска.
        
        Returns:
            bool: True если активна Ириска, False если другой агент
        """
        return self.current_agent == "Ириска"
    
    def can_switch_to_agent(self, agent_name: str) -> Tuple[bool, str]:
        """
        Проверяет, можно ли переключиться на указанного агента.
        
        Args:
            agent_name: Имя агента для переключения
            
        Returns:
            Tuple[bool, str]: (можно ли переключиться, причина)
        """
        try:
            # Проверяем существование агента
            agent = get_agent_profile_by_name(agent_name)
            if not agent:
                return False, f"Агент '{agent_name}' не найден"
            
            # Проверяем статус агента
            if agent.status != "active":
                return False, f"Агент '{agent_name}' неактивен (статус: {agent.status})"
            
            # Ириска может переключаться на любого активного агента
            if self.current_agent == "Ириска":
                return True, "Переключение разрешено"
            
            # Специализированные агенты могут возвращаться только к Ириске
            if agent_name == "Ириска":
                return True, "Возврат к Ириске разрешен"
            
            return False, "Специализированные агенты могут переключаться только на Ириску"
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности переключения: {e}")
            return False, f"Ошибка проверки: {str(e)}"
    
    def switch_to_agent(self, agent_name: str, user_id: str = "default", save_context: bool = True) -> str:
        """
        Переключается на указанного агента.
        
        Процесс переключения:
        1. Сохраняется контекст текущего агента
        2. Деактивируется текущий агент
        3. Активируется новый агент
        4. Обновляется история переключений
        
        Args:
            agent_name: Имя агента для переключения
            user_id: ID пользователя
            save_context: Сохранять ли контекст текущего агента
            
        Returns:
            str: Результат переключения
        """
        try:
            # Проверяем возможность переключения
            can_switch, reason = self.can_switch_to_agent(agent_name)
            if not can_switch:
                return f"❌ Не удалось переключиться на '{agent_name}': {reason}"
            
            # Если переключаемся на того же агента
            if self.current_agent == agent_name:
                return f"ℹ️ Уже работаю как '{agent_name}'"
            
            logger.info(f"🔄 Переключение с '{self.current_agent}' на '{agent_name}'")
            
            # Сохраняем контекст текущего агента
            if save_context and self.current_agent != "Ириска":
                self._save_agent_context(self.current_agent, user_id)
            
            # Деактивируем текущего агента (если это не Ириска)
            if self.current_agent != "Ириска":
                deactivate_result = deactivate_agent(self.current_agent)
                logger.debug(f"Деактивация '{self.current_agent}': {deactivate_result}")
            
            # Сохраняем предыдущего агента для возврата
            if self.current_agent != "Ириска":
                self.previous_agent = self.current_agent
            
            # Активируем нового агента
            activate_result = activate_agent(agent_name, user_id)
            if "❌" in activate_result:
                # Если активация не удалась, возвращаемся к предыдущему агенту
                if self.previous_agent:
                    logger.warning(f"Активация '{agent_name}' не удалась, возвращаюсь к '{self.previous_agent}'")
                    self.current_agent = self.previous_agent
                    self.previous_agent = None
                return f"❌ Ошибка активации агента '{agent_name}': {activate_result}"
            
            # Обновляем текущего агента
            old_agent = self.current_agent
            self.current_agent = agent_name
            
            # Добавляем в историю переключений
            self.switch_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "from": old_agent,
                "to": agent_name,
                "user_id": user_id,
                "success": True
            })
            
            # Ограничиваем размер истории
            if len(self.switch_history) > 100:
                self.switch_history = self.switch_history[-50:]
            
            logger.info(f"✅ Успешно переключился с '{old_agent}' на '{agent_name}'")
            
            # Формируем сообщение о переключении
            if agent_name == "Ириска":
                return f"🎉 **Возвращаюсь к себе!**\n\nПривет, Марат! Я снова Ириска - твой главный AI-менеджер! 🚀\n\nЧто делал {old_agent}? Могу показать его работу или помочь с чем-то другим!"
            else:
                # Получаем информацию о новом агенте
                agent = get_agent_profile_by_name(agent_name)
                if agent:
                    return f"🔄 **Переключился на '{agent_name}'**\n\n📋 Специализация: {agent.specialization or 'не указана'}\n🎯 Назначение: {agent.purpose or 'не указано'}\n\nТеперь ты общаешься с {agent_name}!"
                else:
                    return f"🔄 **Переключился на '{agent_name}'**\n\nТеперь ты общаешься с {agent_name}!"
            
        except Exception as e:
            error_msg = f"❌ Ошибка переключения на '{agent_name}': {str(e)}"
            logger.error(error_msg)
            
            # Добавляем неудачное переключение в историю
            self.switch_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "from": self.current_agent,
                "to": agent_name,
                "user_id": user_id,
                "success": False,
                "error": str(e)
            })
            
            return error_msg
    
    def return_to_iriska(self, user_id: str = "default") -> str:
        """
        Возвращается к Ириске (главному агенту).
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Результат возврата к Ириске
        """
        return self.switch_to_agent("Ириска", user_id)
    
    def return_to_previous_agent(self, user_id: str = "default") -> str:
        """
        Возвращается к предыдущему агенту.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Результат возврата к предыдущему агенту
        """
        if not self.previous_agent:
            return "❌ Нет предыдущего агента для возврата"
        
        return self.switch_to_agent(self.previous_agent, user_id)
    
    def get_switch_history(self, limit: int = 10) -> List[Dict]:
        """
        Получает историю переключений.
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            List[Dict]: История переключений
        """
        return self.switch_history[-limit:] if self.switch_history else []
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных для переключения агентов.
        
        Returns:
            List[Dict]: Список доступных агентов
        """
        try:
            available_agents = []
            
            # Всегда добавляем Ириску
            iriska = get_agent_profile_by_name("Ириска")
            if iriska:
                available_agents.append({
                    "name": "Ириска",
                    "specialization": iriska.specialization or "Главный агент",
                    "purpose": iriska.purpose or "Управление системой",
                    "access_level": iriska.access_level,
                    "is_main_agent": True,
                    "can_switch": True,
                    "reason": "Главный агент"
                })
            
            # Добавляем активных специализированных агентов
            active_agents = get_all_active_agents()
            for agent in active_agents:
                if agent.name != "Ириска":  # Ириску уже добавили
                    can_switch, reason = self.can_switch_to_agent(agent.name)
                    available_agents.append({
                        "name": agent.name,
                        "specialization": agent.specialization or "Не указана",
                        "purpose": agent.purpose or "Не указано",
                        "access_level": agent.access_level,
                        "is_main_agent": False,
                        "can_switch": can_switch,
                        "reason": reason
                    })
            
            return available_agents
            
        except Exception as e:
            logger.error(f"Ошибка получения доступных агентов: {e}")
            return []
    
    def _save_agent_context(self, agent_name: str, user_id: str) -> bool:
        """
        Сохраняет контекст работы агента.
        
        Args:
            agent_name: Имя агента
            user_id: ID пользователя
            
        Returns:
            bool: True если контекст сохранен успешно
        """
        try:
            with SessionLocal() as session:
                # Получаем или создаем контекст агента
                context = session.query(AgentContext).filter_by(
                    agent_name=agent_name,
                    user_id=user_id
                ).first()
                
                if not context:
                    context = AgentContext(
                        agent_name=agent_name,
                        user_id=user_id
                    )
                    session.add(context)
                
                # Сохраняем текущий контекст (здесь можно добавить логику сохранения)
                context.last_updated = datetime.utcnow()
                
                session.commit()
                logger.debug(f"Контекст агента '{agent_name}' сохранен")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения контекста агента '{agent_name}': {e}")
            return False
    
    def _restore_agent_context(self, agent_name: str, user_id: str) -> bool:
        """
        Восстанавливает контекст работы агента.
        
        Args:
            agent_name: Имя агента
            user_id: ID пользователя
            
        Returns:
            bool: True если контекст восстановлен успешно
        """
        try:
            with SessionLocal() as session:
                context = session.query(AgentContext).filter_by(
                    agent_name=agent_name,
                    user_id=user_id
                ).first()
                
                if context:
                    logger.debug(f"Контекст агента '{agent_name}' восстановлен")
                    return True
                else:
                    logger.debug(f"Контекст агента '{agent_name}' не найден")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка восстановления контекста агента '{agent_name}': {e}")
            return False

# ============================================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР МЕНЕДЖЕРА
# ============================================================================

# Создаем глобальный экземпляр менеджера переключения
agent_switcher = AgentSwitcher()

# ============================================================================
# TOOLS ДЛЯ ИРИСКИ ПО УПРАВЛЕНИЮ ПЕРЕКЛЮЧЕНИЕМ
# ============================================================================

def switch_to_agent_tool(agent_name: str, user_id: str = "default") -> str:
    """
    Tool для переключения на указанного агента.
    
    Args:
        agent_name: Имя агента для переключения
        user_id: ID пользователя
        
    Returns:
        str: Результат переключения
    """
    return agent_switcher.switch_to_agent(agent_name, user_id)

def return_to_iriska_tool(user_id: str = "default") -> str:
    """
    Tool для возврата к Ириске.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: Результат возврата
    """
    return agent_switcher.return_to_iriska(user_id)

def return_to_previous_agent_tool(user_id: str = "default") -> str:
    """
    Tool для возврата к предыдущему агенту.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: Результат возврата
    """
    return agent_switcher.return_to_previous_agent(user_id)

def get_current_agent_tool() -> str:
    """
    Tool для получения информации о текущем агенте.
    
    Returns:
        str: Информация о текущем агенте
    """
    current_agent = agent_switcher.get_current_agent()
    
    if current_agent == "Ириска":
        return "👑 **Текущий агент: Ириска**\n\nЯ - главный AI-менеджер системы! У меня есть доступ ко всем tools и функциям. Могу помочь с любыми задачами или переключить тебя на специализированного агента."
    else:
        # Получаем информацию о текущем агенте
        agent = get_agent_profile_by_name(current_agent)
        if agent:
            return f"🤖 **Текущий агент: {current_agent}**\n\n📋 Специализация: {agent.specialization or 'не указана'}\n🎯 Назначение: {agent.purpose or 'не указано'}\n🔒 Права: {agent.access_level}\n\nЧтобы вернуться к Ириске, скажи: 'Вернись к себе' или 'Вернись к Ириске'"
        else:
            return f"🤖 **Текущий агент: {current_agent}**\n\nИнформация об агенте недоступна."

def list_available_agents_tool() -> str:
    """
    Tool для получения списка доступных агентов.
    
    Returns:
        str: Список доступных агентов
    """
    available_agents = agent_switcher.get_available_agents()
    
    if not available_agents:
        return "❌ Нет доступных агентов для переключения"
    
    result = "📋 **Доступные агенты для переключения:**\n\n"
    
    for agent in available_agents:
        # Определяем эмодзи для типа агента
        if agent["is_main_agent"]:
            emoji = "👑"  # Главный агент
        elif "анализ" in agent["specialization"].lower():
            emoji = "📊"  # Аналитик
        elif "креатив" in agent["specialization"].lower():
            emoji = "🎨"  # Креативщик
        else:
            emoji = "🤖"  # Обычный агент
        
        # Определяем статус доступности
        if agent["can_switch"]:
            status = "✅ Доступен"
        else:
            status = f"❌ Недоступен: {agent['reason']}"
        
        result += f"{emoji} **{agent['name']}**\n"
        result += f"   📋 Специализация: {agent['specialization']}\n"
        result += f"   🎯 Назначение: {agent['purpose']}\n"
        result += f"   🔒 Права: {agent['access_level']}\n"
        result += f"   📊 Статус: {status}\n\n"
    
    result += "💡 **Как переключиться:**\n"
    result += "• Скажи: 'Переключись на [имя агента]'\n"
    result += "• Скажи: 'Вернись к себе' для возврата к Ириске\n"
    result += "• Скажи: 'Вернись к предыдущему агенту'\n"
    
    return result

def get_switch_history_tool(limit: int = 10) -> str:
    """
    Tool для получения истории переключений.
    
    Args:
        limit: Максимальное количество записей
        
    Returns:
        str: История переключений
    """
    history = agent_switcher.get_switch_history(limit)
    
    if not history:
        return "📋 История переключений пуста"
    
    result = f"📋 **История переключений (последние {len(history)}):**\n\n"
    
    for i, record in enumerate(reversed(history), 1):
        timestamp = datetime.fromisoformat(record["timestamp"]).strftime("%H:%M:%S")
        
        if record["success"]:
            status = "✅"
            details = f"с '{record['from']}' на '{record['to']}'"
        else:
            status = "❌"
            details = f"на '{record['to']}' (ошибка: {record.get('error', 'неизвестно')})"
        
        result += f"{i}. {status} {timestamp} - {details}\n"
    
    return result

# ============================================================================
# СПИСОК TOOLS ДЛЯ ПЕРЕКЛЮЧЕНИЯ
# ============================================================================

AGENT_SWITCHING_TOOLS = {
    "switch_to_agent": {
        "function": switch_to_agent_tool,
        "description": "Переключается на указанного специализированного агента",
        "parameters": {
            "agent_name": "Имя агента для переключения",
            "user_id": "ID пользователя (опционально)"
        }
    },
    "return_to_iriska": {
        "function": return_to_iriska_tool,
        "description": "Возвращается к Ириске (главному агенту)",
        "parameters": {
            "user_id": "ID пользователя (опционально)"
        }
    },
    "return_to_previous_agent": {
        "function": return_to_previous_agent_tool,
        "description": "Возвращается к предыдущему агенту",
        "parameters": {
            "user_id": "ID пользователя (опционально)"
        }
    },
    "get_current_agent": {
        "function": get_current_agent_tool,
        "description": "Получает информацию о текущем активном агенте",
        "parameters": {}
    },
    "list_available_agents": {
        "function": list_available_agents_tool,
        "description": "Показывает список доступных для переключения агентов",
        "parameters": {}
    },
    "get_switch_history": {
        "function": get_switch_history_tool,
        "description": "Показывает историю переключений между агентами",
        "parameters": {
            "limit": "Максимальное количество записей (по умолчанию 10)"
        }
    }
}

# ============================================================================
# КОНТЕКСТНЫЙ МЕНЕДЖЕР ДЛЯ ВРЕМЕННОГО ПЕРЕКЛЮЧЕНИЯ
# ============================================================================

@contextmanager
def temporary_agent_switch(agent_name: str, user_id: str = "default"):
    """
    Контекстный менеджер для временного переключения на агента.
    
    При выходе из контекста автоматически возвращается к предыдущему агенту.
    
    Args:
        agent_name: Имя агента для временного переключения
        user_id: ID пользователя
        
    Example:
        with temporary_agent_switch("DataAnalyst", "user123"):
            # Здесь работаем как DataAnalyst
            result = analyze_data(data)
        
        # Автоматически возвращаемся к предыдущему агенту
    """
    previous_agent = agent_switcher.get_current_agent()
    
    try:
        # Переключаемся на указанного агента
        switch_result = agent_switcher.switch_to_agent(agent_name, user_id)
        if "❌" in switch_result:
            raise Exception(f"Не удалось переключиться на '{agent_name}': {switch_result}")
        
        logger.info(f"Временно переключился на '{agent_name}'")
        yield agent_switcher
        
    finally:
        # Возвращаемся к предыдущему агенту
        if previous_agent != agent_name:
            return_result = agent_switcher.switch_to_agent(previous_agent, user_id)
            logger.info(f"Вернулся к '{previous_agent}': {return_result}")

# ============================================================================
# ТЕСТИРОВАНИЕ СИСТЕМЫ ПЕРЕКЛЮЧЕНИЯ
# ============================================================================

if __name__ == "__main__":
    print("🧪 Тестирование системы переключения агентов...")
    
    # Тест получения доступных агентов
    print("\n1. Доступные агенты:")
    agents = agent_switcher.get_available_agents()
    for agent in agents:
        print(f"  - {agent['name']}: {agent['specialization']}")
    
    # Тест переключения (если есть тестовый агент)
    print("\n2. Текущий агент:")
    current = agent_switcher.get_current_agent()
    print(f"  Текущий: {current}")
    
    # Тест истории переключений
    print("\n3. История переключений:")
    history = agent_switcher.get_switch_history()
    print(f"  Записей: {len(history)}")
    
    print("\n✅ Тестирование завершено!")
