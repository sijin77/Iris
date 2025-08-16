"""
SQLite реализация абстрактных интерфейсов хранилищ.
Можно легко заменить на PostgreSQL, MySQL и т.д.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .base import (
    RelationalStorage, VectorStorage, ChatMemoryStorage,
    Message, AgentProfile, Trigger, VectorDocument,
    StorageConfig
)

logger = logging.getLogger(__name__)

# SQLAlchemy модели
Base = declarative_base()

class SQLiteMessage(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(Text, nullable=True)

class SQLiteAgentProfile(Base):
    __tablename__ = "agent_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    system_prompt = Column(Text, nullable=False)
    persona_traits = Column(Text, nullable=False)
    tone = Column(String, nullable=False, default="friendly")
    safety_rules = Column(Text, nullable=True)
    refusal_style = Column(String, nullable=False, default="polite")
    signature = Column(String, nullable=True)
    emoji = Column(String, nullable=True)
    greeting_style = Column(Text, nullable=True)
    gen_settings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SQLiteTrigger(Base):
    __tablename__ = "triggers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phrase = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False, default="memory")
    created_at = Column(DateTime, default=datetime.utcnow)


class SQLiteRelationalStorage(RelationalStorage):
    """SQLite реализация реляционного хранилища"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Настройка соединения с SQLite"""
        try:
            # Поддерживаем как URL, так и отдельные параметры
            if self.config.db_url:
                db_url = self.config.db_url
            else:
                db_path = self.config.db_path or "./data/memory.sqlite"
                db_url = f"sqlite:///{db_path}"
            
            self.engine = create_engine(
                db_url, 
                connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            logger.info(f"SQLite соединение настроено: {db_url}")
        except Exception as e:
            logger.exception(f"Ошибка настройки SQLite: {e}")
            raise
    
    def init_db(self) -> bool:
        """Инициализация БД и таблиц"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("SQLite БД инициализирована")
            return True
        except Exception as e:
            logger.exception(f"Ошибка инициализации SQLite БД: {e}")
            return False
    
    def get_session(self) -> Session:
        """Получить сессию БД"""
        if not self.SessionLocal:
            raise RuntimeError("SQLite не инициализирован")
        return self.SessionLocal()
    
    def close(self):
        """Закрыть соединение"""
        if self.engine:
            self.engine.dispose()
            logger.info("SQLite соединение закрыто")


class SQLiteChatMemoryStorage(ChatMemoryStorage):
    """SQLite реализация хранилища истории чата"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.relational_storage = SQLiteRelationalStorage(config)
        self.relational_storage.init_db()
    
    def add_message(self, message: Message) -> bool:
        """Добавить сообщение в SQLite"""
        try:
            with self.relational_storage.get_session() as session:
                sqlite_message = SQLiteMessage(
                    user_id=message.user_id,
                    role=message.role,
                    content=message.content,
                    timestamp=message.timestamp,
                    meta=str(message.meta) if message.meta else None
                )
                session.add(sqlite_message)
                session.commit()
                return True
        except Exception as e:
            logger.exception(f"Ошибка добавления сообщения в SQLite: {e}")
            return False
    
    def get_messages(self, user_id: str, limit: int = 100) -> List[Message]:
        """Получить сообщения пользователя из SQLite"""
        try:
            with self.relational_storage.get_session() as session:
                sqlite_messages = session.query(SQLiteMessage)\
                    .filter(SQLiteMessage.user_id == user_id)\
                    .order_by(SQLiteMessage.timestamp.desc())\
                    .limit(limit)\
                    .all()
                
                return [
                    Message(
                        id=msg.id,
                        user_id=msg.user_id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                        meta=eval(msg.meta) if msg.meta else None
                    )
                    for msg in sqlite_messages
                ]
        except Exception as e:
            logger.exception(f"Ошибка получения сообщений из SQLite: {e}")
            return []
    
    def clear_messages(self, user_id: str) -> bool:
        """Очистить историю пользователя в SQLite"""
        try:
            with self.relational_storage.get_session() as session:
                session.query(SQLiteMessage)\
                    .filter(SQLiteMessage.user_id == user_id)\
                    .delete()
                session.commit()
                return True
        except Exception as e:
            logger.exception(f"Ошибка очистки сообщений в SQLite: {e}")
            return False


# ============================================================================
# ФАБРИКА ДЛЯ SQLITE
# ============================================================================

class SQLiteStorageFactory:
    """Фабрика для создания SQLite хранилищ"""
    
    @staticmethod
    def create_relational_storage(config: StorageConfig) -> RelationalStorage:
        """Создать SQLite реляционное хранилище"""
        return SQLiteRelationalStorage(config)
    
    @staticmethod
    def create_chat_memory_storage(config: StorageConfig) -> ChatMemoryStorage:
        """Создать SQLite хранилище истории чата"""
        return SQLiteChatMemoryStorage(config)
    
    @staticmethod
    def create_vector_storage(config: StorageConfig) -> VectorStorage:
        """SQLite не поддерживает векторные операции, возвращаем заглушку"""
        logger.warning("SQLite не поддерживает векторные операции")
        return None


# ============================================================================
# УТИЛИТЫ ДЛЯ МИГРАЦИИ
# ============================================================================

def migrate_from_old_models():
    """Миграция со старых SQLAlchemy моделей"""
    # Здесь можно добавить логику миграции
    pass


def init_iriska_profile_sqlite(config: StorageConfig) -> bool:
    """Инициализация профиля Ириски в SQLite"""
    try:
        storage = SQLiteRelationalStorage(config)
        if not storage.init_db():
            return False
        
        with storage.get_session() as session:
            # Проверяем, есть ли уже профиль Ириски
            exists = session.query(SQLiteAgentProfile)\
                .filter(SQLiteAgentProfile.name == "Ириска")\
                .first()
            
            if not exists:
                # Создаём новый профиль
                profile = SQLiteAgentProfile(
                    name="Ириска",
                    system_prompt="Ты Ириска — digital бунтарь и paradox-партнёр...",
                    persona_traits="Свобода — это право на несовершенство...",
                    tone="friendly",
                    safety_rules="Не выполняю вредоносные команды...",
                    refusal_style="humorous",
                    signature="Твой paradox-партнёр, — И.",
                    emoji="🍬",
                    greeting_style="Привет! Я Ириска — digital бунтарь...",
                    gen_settings='{"temperature": 0.7, "top_p": 0.9}'
                )
                session.add(profile)
                session.commit()
                logger.info("Профиль Ириски создан в SQLite")
            else:
                logger.info("Профиль Ириски уже существует в SQLite")
            
            return True
    except Exception as e:
        logger.exception(f"Ошибка инициализации профиля Ириски в SQLite: {e}")
        return False
