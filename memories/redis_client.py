import aioredis
from typing import List, Dict, Optional
from datetime import datetime

class RedisClient:
    """
    Класс для работы с Redis, инкапсулирующий все Redis-операции.
    """
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url)
        self.prefix = "memory:v2"  # Можно сделать настраиваемым
    
    async def close(self) -> None:
        """Закрытие соединения с Redis."""
        await self.redis.close()

    # Базовые операции
    async def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Установка значения ключа."""
        await self.redis.set(key, value, ex=ttl)

    async def get_key(self, key: str) -> Optional[str]:
        """Получение значения ключа."""
        return await self.redis.get(key)

    async def delete_key(self, key: str) -> None:
        """Удаление ключа."""
        await self.redis.delete(key)

    async def keys(self, pattern: str) -> List[str]:
        """Поиск ключей по шаблону."""
        return await self.redis.keys(pattern)

    async def memory_usage(self, key: str) -> int:
        """Оценка использования памяти для ключа."""
        return await self.redis.memory_usage(key)

    # Операции с множествами
    async def zadd(self, key: str, mapping: Dict[str, float]) -> None:
        """Добавление элементов в сортированное множество."""
        await self.redis.zadd(key, mapping)

    async def zrangebyscore(self, key: str, min: float, max: float, start: int = 0, num: int = 1000) -> List[str]:
        """Получение элементов по диапазону score."""
        return await self.redis.zrangebyscore(key, min, max, start=start, num=num)

    async def zrevrange(self, key: str, start: int, end: int) -> List[str]:
        """Получение элементов в обратном порядке."""
        return await self.redis.zrevrange(key, start, end)

    async def zrem(self, key: str, member: str) -> None:
        """Удаление элемента из сортированного множества."""
        await self.redis.zrem(key, member)

    # Операции со списками
    async def rpush(self, key: str, value: str) -> None:
        """Добавление элемента в конец списка."""
        await self.redis.rpush(key, value)

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Получение диапазона элементов из списка."""
        return await self.redis.lrange(key, start, end)

    async def llen(self, key: str) -> int:
        """Получение длины списка."""
        return await self.redis.llen(key)

    async def ltrim(self, key: str, start: int, end: int) -> None:
        """Обрезка списка."""
        await self.redis.ltrim(key, start, end)

    # Пайплайн
    async def pipeline(self):
        """Создание конвейера Redis."""
        return self.redis.pipeline()

    # Специфичные методы для работы с памятью
    async def add_fragment(self, fragment_id: str, fragment_data: str, ttl: int, user_id: str, timestamp: float) -> None:
        """Добавление фрагмента в память."""
        pipe = self.pipeline()
        
        # 1. Сохраняем в timeline
        pipe.zadd(f"{self.prefix}:timeline", {fragment_id: timestamp})
        
        # 2. Сохраняем сам фрагмент
        pipe.setex(f"{self.prefix}:fragments:{fragment_id}", ttl, fragment_data)
        
        # 3. Добавляем в диалоговый буфер пользователя
        pipe.rpush(f"{self.prefix}:users:{user_id}:raw", fragment_data)
        
        await pipe.execute()

    async def get_fragments(self, fragment_ids: List[str]) -> List[Optional[str]]:
        """Получение нескольких фрагментов по ID."""
        keys = [f"{self.prefix}:fragments:{fid}" for fid in fragment_ids]
        return await self.redis.mget(keys)

    async def get_user_mode(self, user_id: str) -> str:
        """Получение режима пользователя."""
        mode = await self.get_key(f"{self.prefix}:user:{user_id}:mode")
        return mode.decode() if mode else "default"

    async def set_user_mode(self, user_id: str, mode: str) -> bool:
        """Установка режима пользователя."""
        await self.set_key(f"{self.prefix}:user:{user_id}:mode", mode)
        return True

    async def get_user_raw_messages(self, user_id: str, limit: int = 5) -> List[str]:
        """Получение сырых сообщений пользователя."""
        return await self.lrange(f"{self.prefix}:users:{user_id}:raw", 0, limit - 1)

    async def compress_user_dialogue(self, user_id: str, summary_key: str, summary_data: str, max_history: int) -> None:
        """Сжатие диалога пользователя."""
        pipe = self.pipeline()
        pipe.rpush(summary_key, summary_data)
        pipe.ltrim(summary_key, 0, max_history - 1)
        pipe.delete(f"{self.prefix}:users:{user_id}:raw")
        await pipe.execute()

    async def cache_search(self, cache_key: str, cache_data: str, ttl: int) -> None:
        """Кэширование результатов поиска."""
        await self.set_key(cache_key, cache_data, ttl)

    async def get_cached_search(self, cache_key: str) -> Optional[str]:
        """Получение закэшированных результатов."""
        return await self.get_key(cache_key)

    async def cleanup_expired_fragments(self, batch_size: int = 1000, base_ttl: int = 604800) -> int:
        """Очистка просроченных фрагментов."""
        now = datetime.now().timestamp()
        expired = await self.zrangebyscore(
            f"{self.prefix}:timeline",
            min=0,
            max=now - base_ttl,
            start=0,
            num=batch_size
        )

        if not expired:
            return 0

        # Удаляем пачкой
        pipe = self.pipeline()
        for fid in expired:
            pipe.delete(f"{self.prefix}:fragments:{fid.decode()}")
            pipe.zrem(f"{self.prefix}:timeline", fid.decode())
        await pipe.execute()

        return len(expired)

    async def estimate_memory_usage(self) -> int:
        """Оценка использования памяти."""
        keys = await self.keys(f"{self.prefix}:*")
        return sum(await self.memory_usage(key) for key in keys)