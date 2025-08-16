"""
Главная фабрика для создания хранилищ.
Поддерживает SQLite, ChromaDB и легко расширяется для других БД.
"""

import os
import logging
from typing import Dict, Any, Optional

from .base import StorageConfig, StorageFactory
from .sqlite_storage import SQLiteStorageFactory
from .chroma_storage import ChromaStorageFactory

logger = logging.getLogger(__name__)


class UniversalStorageFactory(StorageFactory):
    """Универсальная фабрика для создания всех типов хранилищ"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._factories = self._register_factories()
    
    def _register_factories(self) -> Dict[str, Any]:
        """Регистрация фабрик для разных типов БД"""
        factories = {}
        
        # Реляционные БД
        if self.config.db_type == "sqlite":
            factories["relational"] = SQLiteStorageFactory
        elif self.config.db_type == "postgresql":
            # TODO: Добавить PostgreSQL фабрику
            logger.warning("PostgreSQL фабрика не реализована, используем SQLite")
            factories["relational"] = SQLiteStorageFactory
        elif self.config.db_type == "mysql":
            # TODO: Добавить MySQL фабрику
            logger.warning("MySQL фабрика не реализована, используем SQLite")
            factories["relational"] = SQLiteStorageFactory
        else:
            logger.warning(f"Неизвестный тип БД: {self.config.db_type}, используем SQLite")
            factories["relational"] = SQLiteStorageFactory
        
        # Векторные БД
        if self.config.vector_type == "chroma":
            factories["vector"] = ChromaStorageFactory
        elif self.config.vector_type == "weaviate":
            # TODO: Добавить Weaviate фабрику
            logger.warning("Weaviate фабрика не реализована, используем ChromaDB")
            factories["vector"] = ChromaStorageFactory
        elif self.config.vector_type == "pinecone":
            # TODO: Добавить Pinecone фабрику
            logger.warning("Pinecone фабрика не реализована, используем ChromaDB")
            factories["vector"] = ChromaStorageFactory
        elif self.config.vector_type == "qdrant":
            # TODO: Добавить Qdrant фабрику
            logger.warning("Qdrant фабрика не реализована, используем ChromaDB")
            factories["vector"] = ChromaStorageFactory
        else:
            logger.warning(f"Неизвестный тип векторной БД: {self.config.vector_type}, используем ChromaDB")
            factories["vector"] = ChromaStorageFactory
        
        # История чата
        if self.config.memory_type == "sqlite":
            factories["memory"] = SQLiteStorageFactory
        elif self.config.memory_type == "redis":
            # TODO: Добавить Redis фабрику
            logger.warning("Redis фабрика не реализована, используем SQLite")
            factories["memory"] = SQLiteStorageFactory
        elif self.config.memory_type == "postgresql":
            # TODO: Добавить PostgreSQL фабрику для памяти
            logger.warning("PostgreSQL фабрика для памяти не реализована, используем SQLite")
            factories["memory"] = SQLiteStorageFactory
        else:
            logger.warning(f"Неизвестный тип памяти: {self.config.memory_type}, используем SQLite")
            factories["memory"] = SQLiteStorageFactory
        
        return factories
    
    def create_relational_storage(self, config: Optional[StorageConfig] = None) -> Any:
        """Создать реляционное хранилище"""
        config = config or self.config
        factory = self._factories.get("relational")
        if factory:
            return factory.create_relational_storage(config)
        else:
            raise ValueError("Реляционная фабрика не зарегистрирована")
    
    def create_vector_storage(self, config: Optional[StorageConfig] = None) -> Any:
        """Создать векторное хранилище"""
        config = config or self.config
        factory = self._factories.get("vector")
        if factory:
            return factory.create_vector_storage(config)
        else:
            raise ValueError("Векторная фабрика не зарегистрирована")
    
    def create_chat_memory_storage(self, config: Optional[StorageConfig] = None) -> Any:
        """Создать хранилище истории чата"""
        config = config or self.config
        factory = self._factories.get("memory")
        if factory:
            return factory.create_chat_memory_storage(config)
        else:
            raise ValueError("Фабрика памяти не зарегистрирована")


# ============================================================================
# КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================================================

def create_storage_config_from_env() -> StorageConfig:
    """Создать конфигурацию хранилищ из переменных окружения"""
    
    # Реляционная БД
    db_type = os.getenv("DB_TYPE", "sqlite")
    db_url = os.getenv("MEMORY_DB_URL")  # Для SQLAlchemy
    db_path = os.getenv("MEMORY_DB_FILE")  # Для файловых БД
    
    # Векторная БД
    vector_type = os.getenv("VECTOR_TYPE", "chroma")
    vector_path = os.getenv("CHROMA_PATH")
    vector_api_key = os.getenv("VECTOR_API_KEY")
    
    # Эмбеддинги
    embedding_type = os.getenv("EMBEDDING_TYPE", "openai")
    embedding_api_key = os.getenv("OPENAI_API_KEY")
    embedding_model = os.getenv("EMBEDDING_MODEL")
    
    # История чата
    memory_type = os.getenv("MEMORY_TYPE", "sqlite")
    memory_path = os.getenv("MEMORY_DB_FILE")
    memory_url = os.getenv("MEMORY_DB_URL")
    
    # Если указан URL для БД, извлекаем параметры
    db_host = None
    db_port = None
    db_name = None
    db_user = None
    db_password = None
    
    if db_url and db_type != "sqlite":
        # Парсим URL вида postgresql://user:pass@host:port/dbname
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            db_host = parsed.hostname
            db_port = parsed.port
            db_name = parsed.path.lstrip('/')
            db_user = parsed.username
            db_password = parsed.password
        except Exception as e:
            logger.warning(f"Не удалось распарсить DB URL: {e}")
    
    return StorageConfig(
        db_type=db_type,
        db_url=db_url,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        vector_type=vector_type,
        vector_path=vector_path,
        vector_api_key=vector_api_key,
        embedding_type=embedding_type,
        embedding_api_key=embedding_api_key,
        embedding_model=embedding_model,
        memory_type=memory_type,
        memory_path=memory_path,
        memory_url=memory_url
    )


# ============================================================================
# СИНГЛТОН ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА
# ============================================================================

class StorageManager:
    """Менеджер глобального доступа к хранилищам"""
    
    _instance = None
    _factory = None
    _storages = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._init_storages()
    
    def _init_storages(self):
        """Инициализация хранилищ"""
        try:
            config = create_storage_config_from_env()
            self._factory = UniversalStorageFactory(config)
            
            # Создаём хранилища
            self._storages["relational"] = self._factory.create_relational_storage()
            self._storages["vector"] = self._factory.create_vector_storage()
            self._storages["memory"] = self._factory.create_chat_memory_storage()
            
            logger.info("StorageManager инициализирован")
            
        except Exception as e:
            logger.exception(f"Ошибка инициализации StorageManager: {e}")
            self._storages = {}
    
    def get_relational_storage(self):
        """Получить реляционное хранилище"""
        return self._storages.get("relational")
    
    def get_vector_storage(self):
        """Получить векторное хранилище"""
        return self._storages.get("vector")
    
    def get_memory_storage(self):
        """Получить хранилище памяти"""
        return self._storages.get("memory")
    
    def get_factory(self):
        """Получить фабрику"""
        return self._factory
    
    def get_config(self):
        """Получить конфигурацию"""
        if self._factory:
            return self._factory.config
        return None


# ============================================================================
# УТИЛИТЫ ДЛЯ БЫСТРОГО ДОСТУПА
# ============================================================================

def get_storage_manager() -> StorageManager:
    """Получить глобальный менеджер хранилищ"""
    return StorageManager()


def get_relational_storage():
    """Быстрый доступ к реляционному хранилищу"""
    return get_storage_manager().get_relational_storage()


def get_vector_storage():
    """Быстрый доступ к векторному хранилищу"""
    return get_storage_manager().get_vector_storage()


def get_memory_storage():
    """Быстрый доступ к хранилищу памяти"""
    return get_storage_manager().get_memory_storage()


def get_storage_config() -> StorageConfig:
    """Быстрый доступ к конфигурации"""
    return get_storage_manager().get_config()
