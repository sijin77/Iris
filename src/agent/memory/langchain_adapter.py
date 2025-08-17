"""
LangChain адаптер для интеграции кэш-системы памяти с LangChain/LangGraph.
Обеспечивает совместимость с существующими LangChain компонентами.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.memory.chat_message_histories import BaseChatMessageHistory

from .models import MemoryFragment, FragmentType, MemoryLevel
from .controller import MemoryController
from .interfaces import IMemoryStorage

logger = logging.getLogger(__name__)


class MemoryControllerChatHistory(BaseChatMessageHistory):
    """
    LangChain совместимая обертка для нашего MemoryController.
    Позволяет использовать кэш-систему как ChatMessageHistory в LangChain.
    """
    
    def __init__(self, memory_controller: MemoryController, user_id: str):
        self.memory_controller = memory_controller
        self.user_id = user_id
        self._messages: List[BaseMessage] = []
        
        logger.info(f"MemoryControllerChatHistory инициализирован для пользователя {user_id}")
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Получает сообщения в формате LangChain"""
        try:
            # Получаем фрагменты из нашего контроллера
            fragments = self._get_fragments_from_controller()
            
            # Конвертируем в LangChain формат
            langchain_messages = []
            for fragment in fragments:
                if fragment.fragment_type == FragmentType.DIALOGUE:
                    # Пользовательское сообщение
                    langchain_messages.append(
                        HumanMessage(content=fragment.content)
                    )
                    
                    # Ответ агента (если есть)
                    if fragment.response:
                        langchain_messages.append(
                            AIMessage(content=fragment.response)
                        )
            
            self._messages = langchain_messages
            return self._messages
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
            return self._messages
    
    def add_user_message(self, message: str) -> None:
        """Добавляет пользовательское сообщение"""
        try:
            fragment = MemoryFragment(
                content=message,
                user_id=self.user_id,
                fragment_type=FragmentType.DIALOGUE,
                priority=self._calculate_message_priority(message)
            )
            
            # Используем наш контроллер для обработки
            import asyncio
            asyncio.create_task(
                self.memory_controller.process_fragment(fragment)
            )
            
            # Добавляем в локальный кэш для LangChain
            self._messages.append(HumanMessage(content=message))
            
            logger.debug(f"Добавлено пользовательское сообщение: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка добавления пользовательского сообщения: {e}")
    
    def add_ai_message(self, message: str) -> None:
        """Добавляет сообщение ИИ"""
        try:
            # Если есть последний фрагмент пользователя, добавляем к нему ответ
            if self._messages and isinstance(self._messages[-1], HumanMessage):
                # Обновляем последний фрагмент с ответом
                # Это упрощенная версия - в реальности нужно найти фрагмент по ID
                pass
            
            # Добавляем в локальный кэш для LangChain
            self._messages.append(AIMessage(content=message))
            
            logger.debug(f"Добавлено сообщение ИИ: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения ИИ: {e}")
    
    def clear(self) -> None:
        """Очищает историю сообщений"""
        try:
            self._messages.clear()
            # Здесь можно добавить логику очистки в нашем контроллере
            logger.info(f"История сообщений очищена для пользователя {self.user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка очистки истории: {e}")
    
    def _get_fragments_from_controller(self) -> List[MemoryFragment]:
        """Получает фрагменты из контроллера памяти"""
        try:
            # Здесь нужна реализация получения фрагментов
            # Пока возвращаем пустой список
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения фрагментов: {e}")
            return []
    
    def _calculate_message_priority(self, message: str) -> float:
        """Вычисляет приоритет сообщения"""
        # Простая эвристика для определения приоритета
        priority = 0.5  # базовый приоритет
        
        # Повышаем приоритет для важных ключевых слов
        important_keywords = [
            "важно", "срочно", "проблема", "ошибка", "помогите",
            "не работает", "критично", "немедленно"
        ]
        
        message_lower = message.lower()
        for keyword in important_keywords:
            if keyword in message_lower:
                priority += 0.1
        
        # Повышаем приоритет для длинных сообщений
        if len(message) > 100:
            priority += 0.1
        
        return min(1.0, priority)


class LangChainMemoryAdapter:
    """
    Адаптер для интеграции нашей кэш-системы с LangChain компонентами.
    """
    
    def __init__(self, memory_controller: MemoryController):
        self.memory_controller = memory_controller
        self._chat_histories: Dict[str, MemoryControllerChatHistory] = {}
        
        logger.info("LangChainMemoryAdapter инициализирован")
    
    def get_chat_history(self, user_id: str) -> MemoryControllerChatHistory:
        """Получает ChatHistory для пользователя"""
        if user_id not in self._chat_histories:
            self._chat_histories[user_id] = MemoryControllerChatHistory(
                self.memory_controller, user_id
            )
        
        return self._chat_histories[user_id]
    
    def create_langchain_memory(self, user_id: str, memory_key: str = "chat_history"):
        """Создает LangChain ConversationBufferMemory с нашим адаптером"""
        try:
            from langchain.memory import ConversationBufferMemory
            
            chat_history = self.get_chat_history(user_id)
            
            return ConversationBufferMemory(
                chat_memory=chat_history,
                return_messages=True,
                memory_key=memory_key
            )
            
        except ImportError:
            logger.error("LangChain не доступен")
            return None
        except Exception as e:
            logger.error(f"Ошибка создания LangChain memory: {e}")
            return None
    
    def get_retriever_for_langchain(self):
        """Создает retriever совместимый с LangChain"""
        try:
            # Здесь нужна интеграция с нашим векторным поиском
            # Пока возвращаем None
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания retriever: {e}")
            return None
    
    async def sync_with_langchain_memory(self, langchain_memory, user_id: str):
        """Синхронизирует состояние с LangChain memory"""
        try:
            if not hasattr(langchain_memory, 'chat_memory'):
                return
            
            # Получаем сообщения из LangChain
            langchain_messages = langchain_memory.chat_memory.messages
            
            # Конвертируем и добавляем в нашу систему
            for message in langchain_messages:
                fragment = MemoryFragment(
                    content=message.content,
                    user_id=user_id,
                    fragment_type=FragmentType.DIALOGUE,
                    priority=0.5
                )
                
                await self.memory_controller.process_fragment(fragment)
            
            logger.info(f"Синхронизировано {len(langchain_messages)} сообщений для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации с LangChain memory: {e}")


# Утилиты для упрощения интеграции

def create_memory_controller_for_langchain(config_dict: Dict[str, Any]) -> MemoryController:
    """Создает MemoryController оптимизированный для работы с LangChain"""
    from .models import MemoryConfig
    
    # Создаем конфигурацию с настройками для LangChain
    config = MemoryConfig(
        # Более агрессивные настройки для интеграции с LangChain
        promotion_threshold=0.6,  # Ниже порог для частого продвижения
        recency_threshold=24.0,   # Больше времени для "свежих" данных
        importance_threshold=0.4,  # Ниже порог важности
        l1_ttl=12.0,             # Короче TTL для L1
        l2_ttl=72.0,             # Короче TTL для L2
        optimization_interval=1800.0,  # Чаще оптимизация (30 мин)
        **config_dict
    )
    
    return MemoryController(config)


def integrate_with_existing_langchain_app(app_memory_components: Dict[str, Any]) -> LangChainMemoryAdapter:
    """
    Интегрирует нашу систему с существующим LangChain приложением.
    
    Args:
        app_memory_components: Словарь с существующими компонентами памяти
        
    Returns:
        Настроенный адаптер для интеграции
    """
    try:
        # Создаем контроллер
        controller = create_memory_controller_for_langchain({})
        
        # Создаем адаптер
        adapter = LangChainMemoryAdapter(controller)
        
        # Инициализируем контроллер
        import asyncio
        asyncio.create_task(controller.initialize())
        
        logger.info("Интеграция с LangChain приложением завершена")
        return adapter
        
    except Exception as e:
        logger.error(f"Ошибка интеграции с LangChain приложением: {e}")
        raise
