"""
# Псевдокод поиска контекста моделью
async def get_context(query):
    wm_context = await working_memory.search(query, limit=5)  # Последние актуальные данные
    ltm_context = await long_term_memory.semantic_search(query)  # Глубокий поиск
    return combine_contexts(wm_context + ltm_context)  # Объединённый результат

TODO Комбинируем контекст для LLM из обеих памятьй
Добавим весовые коэффициенты:
final_context = (
    0.7 * wm_context +  # Новые данные важнее
    0.3 * ltm_context   # Но иногда нужна историческая информация
)
"""


from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Union
import uuid
import asyncio
from pydantic import BaseModel, validator
from prometheus_client import Counter, Gauge, Histogram
from circuitbreaker import circuit
import logging

logger = logging.getLogger(__name__)

# Prometheus метрики
FRAGMENTS_ADDED = Counter('memory_fragments_added', 'Total fragments added')
FRAGMENTS_COMPRESSED = Counter('memory_fragments_compressed', 'Total compression operations')
SEARCH_CACHE_HITS = Counter('memory_search_cache_hits', 'Search cache hits')
SEARCH_CACHE_MISSES = Counter('memory_search_cache_misses', 'Search cache misses')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
PROCESSING_TIME = Histogram('memory_processing_time', 'Fragment processing time')

#TODO разобраться  зачем нам сжимать и использовать векторную бл в рабочей памяти, там же должно быть все
"""
TODO Правило:
"Архивируем не когда нет места, а когда данные достигли ценности"
python
async def archive_policy():
    # По расписанию (каждые 4 часа)
    if time_to_archive():
        await compress_and_save_to_ltm()
    
    # По триггеру важности
    if fragment.priority > 0.8:
        await long_term_memory.save(fragment)
"""

class WorkingMemory:
    """Улучшенная рабочая память с поддержкой эмоциональных режимов и долговременного хранения."""

    def __init__(
        self,
        redis: RedisClient,
        mode_settings: MemoryModeSettings,
        summarizer: Optional[Any] = None,
        base_ttl: int = 604800,  # 7 дней
        vector_db: Optional[Any] = None,
        long_term_memory: Optional[Any] = None
    ):
        """
        Инициализация рабочей памяти.
        
        Args:
            redis: Клиент Redis с вынесенными методами работы
            mode_settings: Настройки режимов работы памяти
            pg_conn: Подключение к PostgreSQL для долговременного хранения
            summarizer: Сервис для сжатия и суммаризации контента
            base_ttl: Базовое время жизни данных в секундах
            vector_db: Клиент векторной базы данных для семантического поиска
        """
        self.redis = redis
        self.summarizer = summarizer
        self.mode_settings = mode_settings
        self.base_ttl = base_ttl
        self.vector_db = vector_db
        self.long_term_memory = long_term_memory
        
        # TODO Продумать позже где  хранитьь и обработать значения низже , нужно добавит в условия сжатия данных
        self.hot_ttl = 24 * 3600  # 1 день для активных данных
        self.cold_ttl = 7 * 86400  # 1 неделя для "остывающих" данных
        self.max_fragments = 10_000  # Лимит фрагментов


    @circuit(failure_threshold=3, recovery_timeout=30)
    @PROCESSING_TIME.time()
    async def add_fragment(self, fragment: MemoryFragment) -> bool:
        """
        Добавляет фрагмент в рабочую память с учетом настроек режима.
        
        Процесс:
        1. Получает текущий режим пользователя
        2. Рассчитывает TTL с учетом приоритета фрагмента и настроек режима
        3. Сохраняет фрагмент в Redis (timeline, raw-буфер и отдельное хранилище)
        4. Проверяет необходимость сжатия диалога
        
        Returns:
            bool: True если было выполнено сжатие диалога, False если нет
        """
        try:
            mode = await self.redis.get_user_mode(fragment.user_id)
            config = self.mode_settings.get_mode_config(mode)
            ttl = int(self.base_ttl * config.ttl_multiplier * fragment.priority)

            # TODO нужна ли Автоматическая модуляция при добавлении
            if fragment.metadata.get("urgent"):
                fragment = self._apply_dopamine(fragment, 0.25)

            await self.redis.add_fragment(
                fragment_id=fragment.id,
                fragment_data=fragment.json(),
                ttl=ttl,
                user_id=fragment.user_id,
                timestamp=fragment.timestamp
            )

            FRAGMENTS_ADDED.inc()
            MEMORY_USAGE.set(await self.redis.estimate_memory_usage())

            # Проверка необходимости сжатия
            if await self.redis.llen(f"{self.redis.prefix}:users:{fragment.user_id}:raw") >= config.threshold:
                await self._compress_dialogue(fragment.user_id, mode)
                FRAGMENTS_COMPRESSED.inc()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to add fragment: {str(e)}", exc_info=True)
            raise

    async def _compress_dialogue(self, user_id: str, mode: str) -> None:
        """
        Сжимает и архивирует текущий диалог пользователя.
        
        Процесс:
        1. Извлекает все сырые сообщения из буфера
        2. Применяет суммаризацию в зависимости от настроек режима
        3. Сохраняет сжатый результат в Redis (summaries)
        4. Очищает raw-буфер
        5. При наличии подключений сохраняет в PostgreSQL и векторную БД
        
        Args:
            user_id: ID пользователя
            mode: Текущий режим работы памяти
        """
        config = self.mode_settings.get_mode_config(mode)
        raw_messages = await self.redis.get_user_raw_messages(user_id)

        if not raw_messages:
            return

        # Создаем базовый сжатый контент
        summary_data = {
            "content": "\n".join(json.loads(msg.decode())["content"] for msg in raw_messages),
            "timestamp": datetime.now().timestamp(),
            "mode": mode
        }

        # Применяем суммаризацию если доступна и нужна
        if self.summarizer and config.compression != "none":
            try:
                dialogues = [json.loads(msg.decode()) for msg in raw_messages]
                summary_data["content"] = await self.summarizer.summarize(
                    dialogues,
                    compression=config.compression,
                    user_id=user_id
                )
            except Exception as e:
                logger.error(f"Summarization failed: {str(e)}")

        # Сохраняем сжатый диалог
        await self.redis.compress_user_dialogue(
            user_id=user_id,
            summary_key=f"{self.redis.prefix}:users:{user_id}:summaries",
            summary_data=json.dumps(summary_data),
            max_history=config.max_history
        )

       
        if self.vector_db:
            await self._save_to_vector_db(user_id, summary_data["content"], mode)
        
        #TODO разобраться когда нужно отправлять в  долгую память
        if should_archive:
            fragment = MemoryFragment(
                id=summary_id,
                content=summary_content,
                timestamp=datetime.now().timestamp()
            )
            await self.long_term_memory.save(fragment)
 
 
 
    async def _save_to_vector_db(self, user_id: str, content: str, mode: str) -> None:
        """
        Индексирует контент в векторной базе данных для семантического поиска.
        
        Args:
            user_id: ID пользователя
            content: Текст для индексации
            mode: Режим работы памяти
        """
        try:
            embedding = await self._generate_embedding(content)
            await self.vector_db.insert(
                collection="memory_fragments",
                vectors=[{
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "metadata": {
                        "user_id": user_id,
                        "mode": mode,
                        "content": content,
                        "timestamp": datetime.now().timestamp()
                    }
                }]
            )
        except Exception as e:
            logger.error(f"Failed to index in vector DB: {str(e)}")

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Генерирует векторное представление текста.
        
        Args:
            text: Текст для векторизации
            
        Returns:
            List[float]: Векторное представление текста
        """
        # Реализация зависит от используемого сервиса
        return []

    async def get_recent_fragments(
        self,
        user_id: str,
        limit: int = 5,
        include_dialogue: bool = True,
        page: int = 1
    ) -> List[MemoryFragment]:
        """
        Получает последние фрагменты памяти с пагинацией.
        
        Процесс:
        1. Получает ID фрагментов из timeline (сортировка по времени)
        2. Загружает содержимое фрагментов
        3. При необходимости добавляет текущие сообщения из диалога
        
        Args:
            user_id: ID пользователя
            limit: Количество возвращаемых фрагментов
            include_dialogue: Включать ли текущий диалог
            page: Номер страницы (для пагинации)
            
        Returns:
            List[MemoryFragment]: Список фрагментов, отсортированных по времени
        """
        offset = (page - 1) * limit
        fragments = []

        # Получаем из timeline
        ids = await self.redis.zrevrange(
            f"{self.redis.prefix}:timeline",
            offset,
            offset + limit - 1
        )

        # Загружаем содержимое
        if ids:
            fragment_data = await self.redis.get_fragments([fid.decode() for fid in ids])
            fragments.extend(
                MemoryFragment.parse_raw(data)
                for data in fragment_data if data
            )

        # Добавляем текущий диалог если нужно
        if include_dialogue:
            raw_messages = await self.redis.get_user_raw_messages(user_id, limit)
            fragments.extend(
                MemoryFragment.parse_raw(msg.decode()) for msg in raw_messages
            )

        return sorted(fragments, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def search_fragments(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Поиск по фрагментам памяти с возможностью кэширования.
        
        Процесс:
        1. Проверяет кэш (если включено)
        2. Выполняет поиск в векторной БД (если доступна)
        3. Или использует ключевой поиск
        4. Кэширует результаты (если включено)
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Максимальное количество результатов
            use_cache: Использовать ли кэширование
            
        Returns:
            List[Dict]: Список найденных фрагментов с метаданными
        """
        # Проверяем кэш
        if use_cache:
            cached = await self._check_search_cache(user_id, query)
            if cached:
                return cached

        # Выполняем поиск
        results = await self._vector_search(user_id, query, limit) if self.vector_db \
            else await self._keyword_search(user_id, query, limit)

        # Кэшируем результаты
        if use_cache and results:
            cache_id = f"search_{uuid.uuid4().hex}"
            await self.redis.cache_search(
                f"{self.redis.prefix}:search_cache:{user_id}:{cache_id}",
                json.dumps({
                    "query": query,
                    "results": results,
                    "timestamp": datetime.now().timestamp(),
                    "metadata": {"user_id": user_id, "source": "memory_search"}
                }),
                ttl=3600
            )

        return results

    async def _check_search_cache(self, user_id: str, query: str) -> Optional[List[Dict]]:
        """
        Проверяет кэш на наличие результатов для похожего запроса.
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            
        Returns:
            Optional[List[Dict]]: Закэшированные результаты или None
        """
        cache_keys = await self.redis.keys(f"{self.redis.prefix}:search_cache:{user_id}:*")
        for key in cache_keys:
            cached = await self.redis.get_cached_search(key)
            if cached:
                data = json.loads(cached)
                if data["query"].lower() == query.lower():
                    SEARCH_CACHE_HITS.inc()
                    return data["results"]
        SEARCH_CACHE_MISSES.inc()
        return None

    async def _vector_search(self, user_id: str, query: str, limit: int) -> List[Dict]:
        """
        Выполняет семантический поиск через векторную БД.
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Dict]: Найденные фрагменты с оценкой релевантности
        """
        try:
            query_embedding = await self._generate_embedding(query)
            results = await self.vector_db.search(
                collection="memory_fragments",
                query_vector=query_embedding,
                top_k=limit,
                filter={"user_id": user_id}
            )
            return [
                {
                    "content": item["metadata"].get("content", ""),
                    "score": item["score"],
                    "timestamp": item["metadata"].get("timestamp")
                }
                for item in results
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []

    async def _keyword_search(self, user_id: str, query: str, limit: int) -> List[Dict]:
        """
        Выполняет поиск по ключевым словам (заглушка).
        
        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Dict]: Пустой список (требует реализации)
        """
        return []

    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """
        Очищает просроченные фрагменты памяти.
        
        Args:
            batch_size: Количество фрагментов для обработки за один раз
            
        Returns:
            int: Количество удаленных фрагментов
        """
        count = await self.redis.cleanup_expired_fragments(batch_size, self.base_ttl)
        MEMORY_USAGE.set(await self.redis.estimate_memory_usage())
        return count

    async def get_user_mode(self, user_id: str) -> str:
        """
        Получает текущий режим работы памяти для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Идентификатор текущего режима
        """
        return await self.redis.get_user_mode(user_id)

    async def set_user_mode(self, user_id: str, mode: str) -> bool:
        """
        Устанавливает режим работы памяти для пользователя.
        
        Args:
            user_id: ID пользователя
            mode: Новый режим
            
        Returns:
            bool: True если режим был установлен, False если режим недопустим
        """
        if mode not in self.mode_settings.modes:
            logger.warning(f"Attempt to set unknown mode: {mode}")
            return False
        return await self.redis.set_user_mode(user_id, mode)