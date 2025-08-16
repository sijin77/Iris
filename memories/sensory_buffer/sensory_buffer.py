"""
SensoryBuffer — это критически важный "фильтр" на входе в систему, выполняющий роль сенсорной памяти (аналог иконической/эхоической памяти в биологии).
1. Основные роли (по аналогии с человеческой памятью):
Биологический аналог	Реализация в коде	Назначение
Рецепторы (глаза/уши)	Внешние API/чаты/датчики	Получение "сырых" сигналов
Сенсорный регистр	SensoryBuffer	Кратковременное удержание и первичная фильтрация
Внимание (attention gate)	importance_threshold=0.3	Отсев незначимой информации
2. Конкретные функции:
1. Быстрый буферизирующий слой

python
# Как работает:
await sensory_buffer.process_input("Сообщение") → Redis Stream (1 сек TTL)
Зачем: Сглаживание "пульсаций" входящего трафика (например, при лавине сообщений)

2. Экстренный фильтр важности

python
# Пример правил:
CRITICAL_WORDS = {"срочно", "ошибка", "alert"}
priority = int("!" in text) * 0.4 + int(any(w in text) for w in CRITICAL_WORDS) * 0.6
Зачем: Немедленное реагирование на критичные сообщения, минуя очередь

3. Защитный барьер

python
# Валидация у нас реализована на уровне модели:
@validator('text')
def validate_text(cls, v):
    if any(tag in v.lower() for tag in ['<script>', '<iframe>']):
        raise ValueError("XSS detected")
Блокирует: XSS, спам, слишком длинные сообщения (>10k символов)

4. Маршрутизатор
python
if fragment.priority >= self.importance_threshold:
    await self._forward_to_working_memory(fragment)
Решает: Какие данные передать в WorkingMemory, а какие отбросить
TODO разобраться c rules
SensoryBuffer(
    redis_client,
    importance_threshold=0.3,  # Порог для WorkingMemory
    buffer_ttl=0.5,            # Полсекунды на обработку
    rules={
        "critical_words": {"взлом", "авария", "urgent"},
        "spam_patterns": [r"http:\/\/.*", r"купите|бесплатно"]  # Регулярки для спама
    }
)
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple
from pydantic import BaseModel, validator
from prometheus_client import Counter, Gauge, Histogram
from circuitbreaker import circuit

# Prometheus metrics
INPUTS_PROCESSED = Counter('sensory_inputs_processed', 'Total processed inputs')
INPUTS_FAILED = Counter('sensory_inputs_failed', 'Failed input processings')
IMPORTANCE_SCORE = Histogram('sensory_importance_score', 'Importance score distribution')
PROCESSING_TIME = Histogram('sensory_processing_time', 'Input processing time')
BUFFER_SIZE = Gauge('sensory_buffer_size', 'Current buffer size')
WM_FORWARD_TIME = Histogram('sensory_wm_forward_time', 'WM forwarding time')


class SensoryInput(BaseModel):
    """
    Модель входных данных сенсорного буфера с валидацией.
    """
    text: str
    timestamp: float
    priority: float = 0.0
    metadata: Dict[str, Any] = {}

    @validator('text')
    def validate_text(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Text must be non-empty string")
        if len(v) > 10_000:
            raise ValueError("Text too long (max 10000 chars)")
        # Basic XSS protection
        if any(tag in v.lower() for tag in ['<script>', '<iframe>', '<img>']):
            raise ValueError("Potential XSS detected")
        return v.strip()

    @validator('priority')
    def validate_priority(cls, v):
        return min(max(v, 0.0), 1.0)


class RedisSensoryBuffer:
    """
    Улучшенная реализация сенсорного буфера на Redis Streams.
    
    Особенности:
    - Батчинговая обработка
    - Circuit breaker для устойчивости
    - Метрики Prometheus
    - Расширенные правила важности
    - Валидация входных данных
    - Adaptive backoff
    
    Args:
        redis_client: Redis клиент
        buffer_ttl: Время жизни данных в буфере (сек)
        importance_threshold: Порог важности
        stream_key: Ключ Redis Stream
        importance_rules: Правила оценки важности
        batch_size: Размер батча для обработки
    """

    DEFAULT_RULES = {
        "length_factor": 0.001,
        "question_mark": 0.3,
        "exclamation_mark": 0.2,
        "critical_word": 0.5,
        "urgent_word": 0.4,
        "mention": 0.25
    }

    CRITICAL_WORDS = {"критично", "срочно", "важно", "error", "alert"}
    URGENT_WORDS = {"срочно", "urgent", "внимание", "attention"}

    def __init__(
        self,
        redis_client: RedisClient,
        working_memory: WorkingMemory,
        buffer_ttl: float = 1.0,
        importance_threshold: float = 0.3,
        stream_key: str = "sensory:raw",
        importance_rules: Optional[Dict[str, float]] = None,
        batch_size: int = 50,
        max_retries: int = 3
    ):
        self.redis = redis_client
        self.stream_key = f"sensory:{stream_key}"  # Namespacing
        self.buffer_ttl = buffer_ttl
        self.importance_threshold = importance_threshold
        self.importance_rules = {**self.DEFAULT_RULES, **(importance_rules or {})}
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._background_task = None
        self._running = False
        self._adaptive_sleep = 0.1  # Initial sleep time
        self._consecutive_empty_reads = 0

    async def start(self) -> None:
        """Запуск фоновой задачи с проверкой подключения."""
        if await self.is_healthy():
            if self._background_task is None:
                self._running = True
                self._background_task = asyncio.create_task(self._background_filter())
                logger.info("Sensory buffer background task started")
        else:
            raise ConnectionError("Redis connection unavailable")

    async def stop(self) -> None:
        """Грациозная остановка с ожиданием завершения."""
        if self._background_task:
            self._running = False
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                logger.info("Background task stopped")
            finally:
                self._background_task = None

    async def is_healthy(self) -> bool:
        """Проверка здоровья буфера и соединения с Redis."""
        try:
            return await self.redis.ping()
        except Exception:
            return False

    @circuit(failure_threshold=3, recovery_timeout=30)
    @PROCESSING_TIME.time()
    async def process_input(self, text: str) -> Optional[SensoryInput]:
        """Обработка входящих данных с повторными попытками."""
        for attempt in range(self.max_retries):
            try:
                fragment = SensoryInput(
                    text=text,
                    timestamp=datetime.now().timestamp(),
                    priority=self._quick_importance_estimate(text),
                    metadata={
                        "source": "direct_input",
                        "processed": False,
                        "attempt": attempt + 1
                    }
                )

                await self.redis.add_to_stream(
                    stream_key=self.stream_key,
                    data=fragment.dict(),
                    expires_at=datetime.now().timestamp() + self.buffer_ttl
                )

                INPUTS_PROCESSED.inc()
                IMPORTANCE_SCORE.observe(fragment.priority)
                BUFFER_SIZE.inc()

                logger.debug(f"Input processed: {fragment.text[:50]}... (priority: {fragment.priority:.2f})")
                return fragment

            except Exception as e:
                if attempt == self.max_retries - 1:
                    INPUTS_FAILED.inc()
                    logger.error(f"Input processing failed after {self.max_retries} attempts: {str(e)}")
                    return None
                await asyncio.sleep(0.1 * (attempt + 1))

    async def _background_filter(self) -> None:
        """Фоновая обработка с adaptive backoff и батчингом."""
        try:
            while self._running:
                try:
                    messages = await self._fetch_messages_batch()
                    
                    if not messages:
                        await self._adjust_sleep_time()
                        continue
                        
                    await self._process_batch(messages)
                    self._reset_sleep_time()
                    
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Background filter stopped normally")
        except Exception as e:
            logger.critical(f"Background filter crashed: {e}")
            raise

    async def _fetch_messages_batch(self) -> List[Tuple[str, Dict]]:
        """Чтение батча сообщений из стрима."""
        try:
            messages = await self.redis.read_stream(
                self.stream_key,
                count=self.batch_size
            )
            if not messages:
                self._consecutive_empty_reads += 1
            return messages
        except Exception as e:
            logger.warning(f"Failed to read stream: {e}")
            return []

    async def _process_batch(self, messages: List[Tuple[str, Dict]]) -> None:
        """Обработка батча сообщений."""
        current_time = datetime.now().timestamp()
        forwarded = 0

        for msg_id, msg_data in messages:
            try:
                fragment = await self._parse_message(msg_data)
                if not fragment:
                    continue

                if (fragment.priority >= self.importance_threshold and 
                    current_time < float(msg_data.get(b"expires_at", 0))):
                    await self._forward_to_working_memory(fragment)
                    forwarded += 1

                await self.redis.delete_from_stream(self.stream_key, msg_id)
                BUFFER_SIZE.dec()

            except Exception as e:
                logger.error(f"Message {msg_id} processing failed: {e}")

        if forwarded:
            logger.debug(f"Forwarded {forwarded}/{len(messages)} messages to WM")

    async def _parse_message(self, msg_data: Dict) -> Optional[SensoryInput]:
        """Парсинг и валидация сообщения."""
        try:
            data = json.loads(msg_data[b"data"])
            return SensoryInput(**data)
        except Exception as e:
            logger.warning(f"Invalid message format: {e}")
            return None

    def _quick_importance_estimate(self, text: str) -> float:
        """Расширенная оценка важности текста. TODO может модель оценивать будет"""
        text_lower = text.lower()
        factors = [
            len(text) * self.importance_rules["length_factor"],
            int("?" in text) * self.importance_rules["question_mark"],
            int("!" in text) * self.importance_rules["exclamation_mark"],
            int(any(w in text_lower for w in self.CRITICAL_WORDS)) * self.importance_rules["critical_word"],
            int(any(w in text_lower for w in self.URGENT_WORDS)) * self.importance_rules["urgent_word"],
            int("@" in text) * self.importance_rules["mention"],
        ]
        return min(max(sum(factors), 0.0), 1.0)

    @WM_FORWARD_TIME.time()
    async def _forward_to_working_memory(self, fragment: SensoryInput) -> None:
        """Передача важных сообщений в рабочую память."""
        try:
            # Конвертируем SensoryInput в MemoryFragment
            wm_fragment = MemoryFragment(
                id=str(uuid.uuid4()),
                user_id="system",  # TODO или другой идентификатор
                content=fragment.text,
                timestamp=fragment.timestamp,
                priority=fragment.priority,
                metadata=fragment.metadata
            )
            
            # Используем API WorkingMemory
            await self.wm.add_fragment(wm_fragment)
            logger.info(f"Forwarded to WM [{fragment.priority:.2f}]: {fragment.text[:100]}...")
        except Exception as e:
            logger.error(f"WM forwarding failed: {e}")

    def _adjust_sleep_time(self) -> None:
        """Adaptive backoff при отсутствии сообщений."""
        if self._consecutive_empty_reads > 5:
            self._adaptive_sleep = min(1.0, self._adaptive_sleep * 1.5)
        return asyncio.sleep(self._adaptive_sleep)

    def _reset_sleep_time(self) -> None:
        """Сброс adaptive sleep при получении сообщений."""
        self._adaptive_sleep = 0.1
        self._consecutive_empty_reads = 0