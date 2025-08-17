"""
ChromaDB реализация абстрактных интерфейсов векторного хранилища.
Можно легко заменить на Weaviate, Pinecone, Qdrant и т.д.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import (
    VectorStorage, VectorDocument, StorageConfig
)

logger = logging.getLogger(__name__)

# ChromaDB импорты с fallback
try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import OpenAIEmbeddings
    CHROMA_AVAILABLE = True
except ImportError:
    try:
        from langchain.vectorstores import Chroma
        from langchain.embeddings import OpenAIEmbeddings
        CHROMA_AVAILABLE = True
    except ImportError:
        CHROMA_AVAILABLE = False
        logger.warning("ChromaDB модули не найдены")


class ChromaVectorStorage(VectorStorage):
    """ChromaDB реализация векторного хранилища"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.vectorstore = None
        self.embeddings = None
        self._setup_storage()
    
    def _setup_storage(self):
        """Настройка ChromaDB хранилища"""
        try:
            if not CHROMA_AVAILABLE:
                raise ImportError("ChromaDB модули недоступны")
            
            # Проверяем наличие API ключа для OpenAI
            if self.config.embedding_type == "openai":
                if not self.config.embedding_api_key:
                    raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
                
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=self.config.embedding_api_key
                )
                logger.info("OpenAI embeddings инициализированы")
            else:
                # Здесь можно добавить другие типы эмбеддингов
                raise NotImplementedError(f"Embedding type {self.config.embedding_type} not supported")
            
            # Настраиваем подключение к ChromaDB
            chromadb_url = os.getenv("CHROMADB_URL")
            
            if chromadb_url:
                # Подключение к удаленному ChromaDB серверу
                import chromadb
                from chromadb.config import Settings
                
                chroma_client = chromadb.HttpClient(
                    host=os.getenv("CHROMADB_HOST", "localhost"),
                    port=int(os.getenv("CHROMADB_PORT", "8000"))
                )
                
                self.vectorstore = Chroma(
                    client=chroma_client,
                    collection_name="iriska_memory",
                    embedding_function=self.embeddings
                )
                logger.info(f"ChromaDB подключен к серверу {chromadb_url}")
            else:
                # Локальное подключение (fallback)
                if self.config.vector_path:
                    persist_directory = self.config.vector_path
                else:
                    persist_directory = "./data/chroma_db"
                
                self.vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings
                )
                logger.info(f"ChromaDB инициализирован локально в {persist_directory}")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации ChromaDB: {e}")
            self.vectorstore = None
            self.embeddings = None
    
    def init_storage(self) -> bool:
        """Инициализация векторного хранилища"""
        return self.vectorstore is not None
    
    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """Добавить документы в ChromaDB"""
        if not self.vectorstore:
            logger.warning("ChromaDB не инициализирован")
            return False
        
        try:
            texts = [doc.text for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            self.vectorstore.add_texts(texts, metadatas=metadatas)
            logger.info(f"Добавлено {len(documents)} документов в ChromaDB")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка добавления документов в ChromaDB: {e}")
            return False
    
    def search_similar(self, query: str, k: int = 4) -> List[VectorDocument]:
        """Поиск похожих документов в ChromaDB"""
        if not self.vectorstore:
            logger.warning("ChromaDB не инициализирован")
            return []
        
        try:
            # Используем LangChain retriever
            retriever = self.vectorstore.as_retriever()
            docs = retriever.get_relevant_documents(query)
            
            # Конвертируем в наши абстрактные документы
            results = []
            for i, doc in enumerate(docs[:k]):
                vector_doc = VectorDocument(
                    id=str(i),
                    text=doc.page_content if hasattr(doc, 'page_content') else str(doc),
                    metadata=doc.metadata if hasattr(doc, 'metadata') else {},
                    embedding=None  # ChromaDB не возвращает эмбеддинги по умолчанию
                )
                results.append(vector_doc)
            
            logger.debug(f"Найдено {len(results)} похожих документов для запроса: {query}")
            return results
            
        except Exception as e:
            logger.exception(f"Ошибка поиска в ChromaDB: {e}")
            return []
    
    def get_by_metadata(self, filters: Dict[str, Any]) -> List[VectorDocument]:
        """Поиск документов по метаданным в ChromaDB"""
        if not self.vectorstore:
            logger.warning("ChromaDB не инициализирован")
            return []
        
        try:
            # Получаем все документы с метаданными
            result = self.vectorstore.get(include=['metadatas', 'documents'])
            
            documents = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            # Фильтруем по метаданным
            filtered_docs = []
            for doc, meta in zip(documents, metadatas):
                # Проверяем, что все фильтры совпадают
                if all(meta.get(key) == value for key, value in filters.items()):
                    vector_doc = VectorDocument(
                        id=str(len(filtered_docs)),
                        text=doc,
                        metadata=meta,
                        embedding=None
                    )
                    filtered_docs.append(vector_doc)
            
            logger.debug(f"Найдено {len(filtered_docs)} документов по фильтрам: {filters}")
            return filtered_docs
            
        except Exception as e:
            logger.exception(f"Ошибка поиска по метаданным в ChromaDB: {e}")
            return []
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Удалить документы из ChromaDB"""
        if not self.vectorstore:
            logger.warning("ChromaDB не инициализирован")
            return False
        
        try:
            # ChromaDB поддерживает удаление по ID
            # Но нужно сначала получить документы по ID
            # Это упрощённая реализация
            logger.info(f"Удаление {len(document_ids)} документов из ChromaDB")
            # TODO: Реализовать корректное удаление по ID
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка удаления документов из ChromaDB: {e}")
            return False


# ============================================================================
# ФАБРИКА ДЛЯ CHROMADB
# ============================================================================

class ChromaStorageFactory:
    """Фабрика для создания ChromaDB хранилищ"""
    
    @staticmethod
    def create_vector_storage(config: StorageConfig) -> Optional[VectorStorage]:
        """Создать ChromaDB векторное хранилище"""
        try:
            return ChromaVectorStorage(config)
        except Exception as e:
            logger.error(f"Ошибка создания ChromaDB хранилища: {e}")
            return None


# ============================================================================
# АДАПТЕРЫ ДЛЯ СОВМЕСТИМОСТИ
# ============================================================================

class ChromaAdapter:
    """Адаптер для совместимости со старым кодом"""
    
    def __init__(self, config: StorageConfig):
        self.vector_storage = ChromaVectorStorage(config)
        self.retriever = None
        self._setup_retriever()
    
    def _setup_retriever(self):
        """Настройка LangChain retriever для совместимости"""
        if self.vector_storage.vectorstore:
            self.retriever = self.vector_storage.vectorstore.as_retriever()
    
    def save_summary_to_chroma(self, summary_data: Dict[str, Any]) -> bool:
        """Совместимость со старым кодом"""
        try:
            doc = VectorDocument(
                id=None,
                text=summary_data.get("summary", ""),
                metadata={"timestamp": summary_data.get("timestamp", "")}
            )
            return self.vector_storage.add_documents([doc])
        except Exception as e:
            logger.error(f"Ошибка сохранения summary в ChromaDB: {e}")
            return False
    
    def get_summaries_by_period(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Совместимость со старым кодом"""
        try:
            filters = {
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            docs = self.vector_storage.get_by_metadata(filters)
            
            return [
                {
                    "summary": doc.text,
                    "timestamp": doc.metadata.get("timestamp", "")
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Ошибка поиска summary по периоду: {e}")
            return []
    
    def get_relevant_documents(self, query: str, k: int = 4) -> List[Any]:
        """Совместимость со старым кодом"""
        try:
            docs = self.vector_storage.search_similar(query, k)
            # Возвращаем в формате, ожидаемом LangChain
            return [doc.text for doc in docs]
        except Exception as e:
            logger.error(f"Ошибка поиска релевантных документов: {e}")
            return []


# ============================================================================
# КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ
# ============================================================================

def get_default_chroma_config() -> StorageConfig:
    """Получить конфигурацию ChromaDB по умолчанию"""
    return StorageConfig(
        vector_type="chroma",
        vector_path="./data/chroma_db",
        embedding_type="openai",
        embedding_api_key=os.getenv("OPENAI_API_KEY")
    )
