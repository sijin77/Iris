# TODO (retriever):
# - Заменить OpenAIEmbeddings на локальные эмбеддинги (например, Instructor/Embeddings)
# - Пайплайн индексации: чанкование, метаданные, обновления, удаление
# - Конфигурация Chroma: из переменных окружения, миграции
# - Поиск с фильтрами по метаданным и периодам времени
# - Тесты на индексацию, поиск и деградацию при отсутствии эмбеддингов

import os
import logging
logger = logging.getLogger(__name__)
from agent.memory import working_memory

# Путь к ChromaDB
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# Инициализируем ChromaDB только если доступны все зависимости
retriever = None
vectorstore = None

try:
    # Проверяем наличие OpenAI API ключа
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.info("OPENAI_API_KEY не найден, ChromaDB отключен")
        raise ValueError("OPENAI_API_KEY required for ChromaDB")
    
    # Импортируем зависимости
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import OpenAIEmbeddings
    except ImportError:
        try:
            from langchain.vectorstores import Chroma
            from langchain.embeddings import OpenAIEmbeddings
        except ImportError:
            logger.warning("LangChain модули не найдены, ChromaDB отключен")
            raise ImportError("LangChain modules not found")
    
    # Создаём OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    # Создаём ChromaDB vectorstore
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
    
    # Retriever для LangChain
    retriever = vectorstore.as_retriever()
    logger.info(f"ChromaDB инициализирован в {CHROMA_PATH}")
    
except Exception as e:
    logger.info(f"ChromaDB отключен: {e}")
    retriever = None
    vectorstore = None

def save_summary_to_chroma():
    """Сохраняет summary в ChromaDB, если доступен"""
    if not retriever:
        logger.debug("ChromaDB недоступен, summary не сохранён")
        return
    
    try:
        data = working_memory.export_summary_for_chroma()
        retriever.vectorstore.add_texts([data["summary"]], metadatas=[{"timestamp": data["timestamp"]}])
        logger.info(f"Summary успешно сохранён в ChromaDB с таймкодом {data['timestamp']}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении summary в ChromaDB: {e}")

def get_summaries_by_period(start_time: str, end_time: str):
    """
    Возвращает summary из ChromaDB, у которых timestamp попадает в указанный период (ISO8601 строки).
    """
    if not retriever:
        logger.debug("ChromaDB недоступен, возвращаем пустой список")
        return []
    
    try:
        # Получаем все документы с метаданными
        docs = retriever.vectorstore.get(include=['metadatas', 'documents'])
        results = []
        for doc, meta in zip(docs['documents'], docs['metadatas']):
            ts = meta.get('timestamp')
            if ts and start_time <= ts <= end_time:
                results.append({
                    'summary': doc,
                    'timestamp': ts
                })
        return results
    except Exception as e:
        logger.error(f"Ошибка при поиске summary по периоду: {e}")
        return []

def get_relevant_documents(query: str, k: int = 4):
    """
    Получает релевантные документы из ChromaDB для запроса.
    
    Args:
        query: Поисковый запрос
        k: Количество документов для возврата
        
    Returns:
        Список релевантных документов или пустой список
    """
    if not retriever:
        logger.debug("ChromaDB недоступен, возвращаем пустой список документов")
        return []
    
    try:
        docs = retriever.get_relevant_documents(query)
        return docs[:k]
    except Exception as e:
        logger.error(f"Ошибка при поиске релевантных документов: {e}")
        return [] 