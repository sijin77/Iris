"""
Базовые абстрактные интерфейсы для хранилищ.
Позволяют легко заменить конкретные реализации БД.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass


# ============================================================================
# БАЗОВЫЕ ТИПЫ ДАННЫХ
# ============================================================================

@dataclass
class Message:
    """Абстрактное сообщение чата"""
    id: Optional[int]
    user_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    meta: Optional[Dict[str, Any]] = None


@dataclass
class AgentProfile:
    """Абстрактный профиль агента"""
    id: Optional[int]
    name: str
    system_prompt: str
    persona_traits: str
    tone: str
    safety_rules: Optional[str] = None
    refusal_style: str = "polite"
    signature: Optional[str] = None
    emoji: Optional[str] = None
    greeting_style: Optional[str] = None
    gen_settings: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Trigger:
    """Абстрактный триггер"""
    id: Optional[int]
    phrase: str
    type: str  # "memory", "emotion", "style"
    created_at: Optional[datetime] = None


@dataclass
class VectorDocument:
    """Абстрактный документ для векторного поиска"""
    id: Optional[str]
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


# ============================================================================
# АБСТРАКТНЫЕ ИНТЕРФЕЙСЫ ХРАНИЛИЩ
# ============================================================================

class RelationalStorage(ABC):
    """Абстрактный интерфейс для реляционных БД (SQLite, PostgreSQL)"""
    
    @abstractmethod
    def init_db(self) -> bool:
        """Инициализация БД и таблиц"""
        pass
    
    @abstractmethod
    def get_session(self):
        """Получить сессию БД"""
        pass
    
    @abstractmethod
    def close(self):
        """Закрыть соединение"""
        pass


class VectorStorage(ABC):
    """Абстрактный интерфейс для векторных БД (ChromaDB, Weaviate)"""
    
    @abstractmethod
    def init_storage(self) -> bool:
        """Инициализация векторного хранилища"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """Добавить документы"""
        pass
    
    @abstractmethod
    def search_similar(self, query: str, k: int = 4) -> List[VectorDocument]:
        """Поиск похожих документов"""
        pass
    
    @abstractmethod
    def get_by_metadata(self, filters: Dict[str, Any]) -> List[VectorDocument]:
        """Поиск по метаданным"""
        pass
    
    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Удалить документы"""
        pass


class ChatMemoryStorage(ABC):
    """Абстрактный интерфейс для истории чата"""
    
    @abstractmethod
    def add_message(self, message: Message) -> bool:
        """Добавить сообщение"""
        pass
    
    @abstractmethod
    def get_messages(self, user_id: str, limit: int = 100) -> List[Message]:
        """Получить сообщения пользователя"""
        pass
    
    @abstractmethod
    def clear_messages(self, user_id: str) -> bool:
        """Очистить историю пользователя"""
        pass


# ============================================================================
# ФАБРИКИ ДЛЯ СОЗДАНИЯ ХРАНИЛИЩ
# ============================================================================

class StorageFactory(ABC):
    """Абстрактная фабрика для создания хранилищ"""
    
    @abstractmethod
    def create_relational_storage(self, config: Dict[str, Any]) -> RelationalStorage:
        """Создать реляционное хранилище"""
        pass
    
    @abstractmethod
    def create_vector_storage(self, config: Dict[str, Any]) -> VectorStorage:
        """Создать векторное хранилище"""
        pass
    
    @abstractmethod
    def create_chat_memory_storage(self, config: Dict[str, Any]) -> ChatMemoryStorage:
        """Создать хранилище истории чата"""
        pass


# ============================================================================
# КОНФИГУРАЦИЯ ХРАНИЛИЩ
# ============================================================================

@dataclass
class StorageConfig:
    """Конфигурация для хранилищ"""
    
    # Реляционная БД
    db_type: str = "sqlite"  # "sqlite", "postgresql", "mysql"
    db_url: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    
    # Векторная БД
    vector_type: str = "chroma"  # "chroma", "weaviate", "pinecone", "qdrant"
    vector_url: Optional[str] = None
    vector_path: Optional[str] = None
    vector_api_key: Optional[str] = None
    
    # Эмбеддинги
    embedding_type: str = "openai"  # "openai", "sentence-transformers", "instructor"
    embedding_api_key: Optional[str] = None
    embedding_model: Optional[str] = None
    
    # История чата
    memory_type: str = "sqlite"  # "sqlite", "redis", "postgresql"
    memory_path: Optional[str] = None
    memory_url: Optional[str] = None


# ============================================================================
# УТИЛИТЫ ДЛЯ КОНВЕРТАЦИИ
# ============================================================================

def convert_sqlalchemy_to_abstract(orm_obj) -> Any:
    """Конвертировать SQLAlchemy объект в абстрактный"""
    if hasattr(orm_obj, '__dict__'):
        return orm_obj.__dict__
    return orm_obj


def convert_abstract_to_sqlalchemy(abstract_obj, orm_class) -> Any:
    """Конвертировать абстрактный объект в SQLAlchemy"""
    if hasattr(orm_class, '__init__'):
        return orm_class(**abstract_obj.__dict__)
    return abstract_obj
