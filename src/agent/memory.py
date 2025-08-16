"""
Модуль для управления памятью агента.
Включает краткосрочную память (история чата) и долгосрочную память (важные сообщения).
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Попытка импорта с fallback для разных версий LangChain
try:
    # Новая версия LangChain
    from langchain_community.memory.chat_message_histories import SQLiteChatMessageHistory
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Старая версия LangChain
        from langchain.memory.chat_message_histories import SQLiteChatMessageHistory
        from langchain.memory import ConversationBufferMemory
        from langchain.schema import BaseMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        # Fallback если LangChain недоступен
        LANGCHAIN_AVAILABLE = False
        SQLiteChatMessageHistory = None
        ConversationBufferMemory = None
        BaseMessage = None

from agent.emotions import analyze_emotion

logger = logging.getLogger(__name__)

# Путь к базе данных для истории
MEMORY_DB_FILE = os.getenv("MEMORY_DB_FILE", "./memory.sqlite")

# Инициализация памяти с проверкой доступности LangChain
if LANGCHAIN_AVAILABLE and SQLiteChatMessageHistory:
    try:
        # Инициализируем SQLite историю чата
        chat_history = SQLiteChatMessageHistory(
            database_path=os.getenv("MEMORY_DB_FILE", "chat_history.db")
        )
        
        # Создаём память для разговора
        memory = ConversationBufferMemory(
            chat_memory=chat_history,
            return_messages=True,
            memory_key="chat_history"
        )
        
        logger.info("LangChain память инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации LangChain памяти: {e}")
        # Fallback: простая память без базы данных
        memory = None
        chat_history = None
else:
    logger.warning("LangChain недоступен, память отключена")
    memory = None
    chat_history = None

# Суммаризатор опциональный - не блокирует запуск
summarizer = None
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")
    logger.info("Суммаризатор T5 инициализирован")
except ImportError:
    logger.info("Модуль transformers не найден, суммаризация отключена")
except Exception as e:
    logger.warning(f"Ошибка инициализации суммаризатора: {e}")

# TODO (memory):
# - ✅ Развести переменные: отдельный путь файла для LangChain и URL для SQLAlchemy
# - ✅ Сделать суммаризацию опциональной/асинхронной или локальной без heavy моделей
# - Лимиты на объём памяти, политики очистки/ретенции, приватность
# - Перенос важных сообщений в БД, индексация для RAG
# - Тесты на определение важности и на корректность экспорта в Chroma

class WorkingMemory:
    def __init__(self):
        self.important_messages = []
        self.current_style = "neutral"  # "serious", "funny", ...
        self.current_emotion = "neutral"

    def add_message(self, message, emotion=None, style=None):
        if self.is_important(message):
            self.important_messages.append({
                "text": message,
                "emotion": emotion or analyze_emotion(message),
                "style": style or self.current_style,
                "timestamp": datetime.utcnow().isoformat()
            })
        if style:
            self.current_style = style
        if emotion:
            self.current_emotion = emotion

    def is_important(self, message):
        important_triggers = [
            "решили", "итог", "вывод", "план", "стратегия", "переключаемся", "серьёзно", "шутки"
        ]
        return any(trigger in message.lower() for trigger in important_triggers)

    def summarize(self):
        if not self.important_messages:
            return "[Нет важных сообщений для суммаризации]"
        
        if not summarizer:
            # Простая суммаризация без ML модели
            messages = [msg["text"] for msg in self.important_messages[-3:]]  # Последние 3
            return f"Ключевые моменты: {'; '.join(messages[:2])}"
        
        try:
            text = " ".join([msg["text"] for msg in self.important_messages])
            summary = summarizer(text, max_length=60, min_length=10, do_sample=False)[0]["summary_text"]
            return summary
        except Exception as e:
            logger.error(f"Ошибка ML суммаризации: {e}")
            # Fallback на простую суммаризацию
            messages = [msg["text"] for msg in self.important_messages[-3:]]
            return f"Ключевые моменты: {'; '.join(messages[:2])}"

    def export_summary_for_chroma(self):
        # Экспортирует summary с таймкодом для ChromaDB
        summary = self.summarize()
        if self.important_messages:
            last_time = self.important_messages[-1]["timestamp"]
        else:
            last_time = datetime.utcnow().isoformat()
        return {
            "summary": summary,
            "timestamp": last_time
        }

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает последние сообщения из памяти."""
        try:
            # Получаем из рабочей памяти
            working_msgs = self.important_messages[-limit:]
            
            # Объединяем и сортируем по времени
            all_msgs = working_msgs
            all_msgs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return all_msgs[:limit]
        except Exception as e:
            logger.error(f"Ошибка получения сообщений из рабочей памяти: {e}")
            return []

working_memory = WorkingMemory() 

def add_message(message: str, role: str = "user", emotion: str = None, style: str = None) -> bool:
    """Добавляет сообщение в память."""
    try:
        # Добавляем в рабочую память
        working_memory.add_message(message, role, emotion, style)
        
        # Добавляем в LangChain память если доступна
        if memory and chat_history:
            if role == "user":
                chat_history.add_user_message(message)
            elif role == "assistant":
                chat_history.add_ai_message(message)
            logger.debug(f"Сообщение добавлено в LangChain память: {role}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления сообщения в память: {e}")
        return False 

def get_messages(limit: int = 10) -> List[Dict[str, Any]]:
    """Получает последние сообщения из памяти."""
    try:
        # Получаем из рабочей памяти
        working_msgs = working_memory.get_recent_messages(limit)
        
        # Получаем из LangChain памяти если доступна
        langchain_msgs = []
        if memory and chat_history:
            try:
                langchain_msgs = memory.chat_memory.messages[-limit:] if memory.chat_memory.messages else []
                # Конвертируем в наш формат
                langchain_msgs = [
                    {
                        "role": "user" if hasattr(msg, 'type') and msg.type == 'human' else "assistant",
                        "content": msg.content if hasattr(msg, 'content') else str(msg),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for msg in langchain_msgs
                ]
            except Exception as e:
                logger.warning(f"Ошибка получения сообщений из LangChain: {e}")
        
        # Объединяем и сортируем по времени
        all_msgs = working_msgs + langchain_msgs
        all_msgs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return all_msgs[:limit]
    except Exception as e:
        logger.error(f"Ошибка получения сообщений: {e}")
        return working_memory.get_recent_messages(limit) 