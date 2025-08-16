import aioredis
from typing import Optional, Dict, Any
import json
from datetime import datetime
import asyncio
from pydantic import BaseModel
from logging import getLogger

logger = getLogger(__name__)

class RedisClient:
    """
    Класс для работы с Redis, инкапсулирующий все Redis-операции.
    
    Args:
        redis_url: URL подключения к Redis
    """
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url)
    
    async def add_to_stream(
        self,
        stream_key: str,
        data: Dict[str, Any],
        expires_at: Optional[float] = None
    ) -> None:
        """
        Добавление данных в Redis Stream.
        
        Args:
            stream_key: Ключ стрима
            data: Данные для добавления
            expires_at: Время истечения (timestamp)
        """
        fields = {"data": json.dumps(data)}
        if expires_at is not None:
            fields["expires_at"] = str(expires_at)
        await self.redis.xadd(stream_key, fields)
    
    async def read_stream(
        self,
        stream_key: str,
        last_id: str = "0-0",
        count: int = 100,
        block: int = 100
    ) -> Optional[list]:
        """
        Чтение данных из Redis Stream.
        
        Args:
            stream_key: Ключ стрима
            last_id: ID последнего сообщения
            count: Максимальное количество сообщений
            block: Время блокировки (мс)
            
        Returns:
            Список сообщений или None
        """
        messages = await self.redis.xread(
            streams={stream_key: last_id},
            count=count,
            block=block
        )
        return messages[0][1] if messages else None
    
    async def delete_from_stream(
        self,
        stream_key: str,
        message_id: str
    ) -> None:
        """
        Удаление сообщения из Redis Stream.
        
        Args:
            stream_key: Ключ стрима
            message_id: ID сообщения
        """
        await self.redis.xdel(stream_key, message_id)
    
    async def set_key(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Установка значения ключа.
        
        Args:
            key: Ключ
            value: Значение
            ttl: Время жизни (сек)
        """
        await self.redis.set(key, value, ex=ttl)
    
    async def close(self) -> None:
        """
        Закрытие соединения с Redis.
        """
        await self.redis.close()


class SensoryInput(BaseModel):
    """
    Модель входных данных сенсорного буфера.
    """
    text: str
    timestamp: float
    priority: float = 0.0
    metadata: Dict[str, Any] = {}


class RedisSensoryBuffer:
    """
    Реализация сенсорного буфера на Redis Streams.
    - Быстрая оценка важности
    - Фоновая фильтрация и передача важных данных
    - Асинхронный интерфейс
    
    Args:
        redis_url: URL подключения к Redis
        buffer_ttl: Время жизни данных в буфере (сек)
        importance_threshold: Порог важности для передачи в рабочую память
        stream_key: Ключ Redis Stream для хранения данных
        importance_rules: Правила оценки важности

    """
    def __init__(
        self,
        redis_client: RedisClient,
        buffer_ttl: float = 1.0,
        importance_threshold: float = 0.3,
        stream_key: str = "sensory:raw",
        importance_rules: Optional[Dict[str, float]] = None
    ):
        self.redis = redis_client
        self.stream_key = stream_key
        self.buffer_ttl = buffer_ttl
        self.importance_threshold = importance_threshold
        self.importance_rules = importance_rules or {
            "length_factor": 0.001,
            "question_mark": 0.3,
            "exclamation_mark": 0.2,
            "critical_word": 0.5
        }
        self._background_task = None
        self._running = False

    async def start(self) -> None:
        """Запуск фоновой задачи обработки."""
        if self._background_task is None:
            self._running = True
            self._background_task = asyncio.create_task(self._background_filter())
            logger.info("Sensory buffer background task started")

    async def stop(self) -> None:
        """
        Корректная остановка фоновой задачи.
        Должен быть вызван при завершении работы системы.
        """
        if self._background_task:
            self._running = False
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                logger.info("Sensory buffer background task stopped")
            finally:
                self._background_task = None

    async def process_input(self, text: str) -> Optional[SensoryInput]:
        """Основной метод обработки входящих данных."""
        try:
            fragment = SensoryInput(
                text=text,
                timestamp=datetime.now().timestamp(),
                priority=self._quick_importance_estimate(text),
                metadata={"source": "direct_input", "processed": False}
            )
            
            await self.redis.add_to_stream(
                stream_key=self.stream_key,
                data=fragment.dict(),
                expires_at=datetime.now().timestamp() + self.buffer_ttl
            )
            
            logger.debug(f"Input processed: {fragment.text[:50]}... (priority: {fragment.priority:.2f})")
            return fragment
            
        except Exception as e:
            logger.error(f"Input processing failed: {str(e)}", exc_info=True)
            return None

    async def _background_filter(self) -> None:
        """
        Фоновая задача для фильтрации и обработки данных.
        
        Основные функции:
        1. Чтение данных из стрима
        2. Фильтрация по важности
        3. Передача важных данных в рабочую память
        4. Удаление обработанных данных
        """
        try:
            while self._running:
                try:
                    messages = await self.redis.read_stream(self.stream_key)
                    
                    if not messages:
                        await asyncio.sleep(0.1)
                        continue
                        
                    for msg_id, msg_data in messages:
                        try:
                            fragment = SensoryInput(**json.loads(msg_data[b"data"]))
                            current_time = datetime.now().timestamp()
                            expires_at = float(msg_data.get(b"expires_at", 0))
                            
                            if (fragment.priority >= self.importance_threshold and 
                                current_time < expires_at):
                                await self._forward_to_working_memory(fragment)
                                
                            await self.redis.delete_from_stream(self.stream_key, msg_id)
                            
                        except Exception as msg_error:
                            logger.error(f"Message processing failed: {msg_error}")
                            
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Background filter error: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Background filter stopped normally")
        except Exception as e:
            logger.critical(f"Background filter crashed: {e}")

    def _quick_importance_estimate(self, text: str) -> float:
        """
        Быстрая эвристическая оценка важности текста.
        Returns:
            float: Оценка важности (0.0-1.0)
        """
        text_lower = text.lower()
        factors = [
            len(text) * self.importance_rules["length_factor"],
            int("?" in text) * self.importance_rules["question_mark"],
            int("!" in text) * self.importance_rules["exclamation_mark"],
            int("критично" in text_lower) * self.importance_rules["critical_word"],
        ]
        return min(max(sum(factors), 0.0), 1.0)

    async def _forward_to_working_memory(self, fragment: SensoryInput) -> None:
        """Передача фрагмента в рабочую память."""
        try:
            await self.redis.set_key(
                f"working:fragment:{fragment.timestamp}",
                fragment.json(),
                ttl=7 * 24 * 3600
            )
            logger.info(f"Forwarded to WM: {fragment.text[:100]}...")
        except Exception as e:
            logger.error(f"Failed to forward to WM: {e}")


async def main():
    # Создаем клиент Redis и передаем его в буфер
    redis_client = RedisClient(redis_url="redis://localhost")
    buffer = RedisSensoryBuffer(
        redis_client=redis_client,
        importance_threshold=0.4,
        importance_rules={"critical_word": 0.7}
    )
    
    await buffer.start()
    
    try:
        await buffer.process_input("Важное сообщение!")
        await asyncio.sleep(2)
    finally:
        await buffer.stop()
        await redis_client.close()