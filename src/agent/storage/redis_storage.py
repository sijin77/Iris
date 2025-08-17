"""
Redis реализация для новой архитектуры памяти (L1 - Hot Cache).
Интегрируется с существующим RedisClient из memories/redis_client.py.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..memory.models import MemoryFragment, MemoryLevel
from ..memory.interfaces import IMemoryStorage
from ...memories.redis_client import RedisClient

logger = logging.getLogger(__name__)


class RedisMemoryStorage(IMemoryStorage):
    """Redis реализация для L1 горячего кэша"""
    
    def __init__(self, redis_url: str = None, redis_db: int = 0):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_db = redis_db
        self.redis_client = RedisClient(self.redis_url)
        self.prefix = "memory_cache:v3"  # Новый префикс для архитектуры памяти
        
    async def init_storage(self) -> bool:
        """Инициализация Redis хранилища"""
        try:
            # Проверяем подключение
            await self.redis_client.set_key(f"{self.prefix}:health", "ok", 10)
            health = await self.redis_client.get_key(f"{self.prefix}:health")
            
            if health:
                logger.info("Redis хранилище инициализировано успешно")
                return True
            else:
                logger.error("Не удалось проверить Redis подключение")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации Redis хранилища: {e}")
            return False
    
    async def store_fragment(self, fragment: MemoryFragment) -> bool:
        """Сохранить фрагмент памяти в Redis"""
        try:
            fragment_key = f"{self.prefix}:fragments:{fragment.id}"
            
            # Сериализуем фрагмент в JSON
            fragment_data = {
                "id": fragment.id,
                "content": fragment.content,
                "metadata": fragment.metadata,
                "timestamp": fragment.timestamp.isoformat(),
                "priority": fragment.priority,
                "fragment_type": fragment.fragment_type.value,
                "level": fragment.level.value,
                "access_count": fragment.access_count,
                "last_accessed": fragment.last_accessed.isoformat() if fragment.last_accessed else None,
                "created_at": fragment.created_at.isoformat()
            }
            
            # Определяем TTL на основе приоритета и уровня
            ttl = self._calculate_ttl(fragment)
            
            # Сохраняем фрагмент
            await self.redis_client.set_key(
                fragment_key,
                json.dumps(fragment_data, ensure_ascii=False),
                ttl
            )
            
            # Добавляем в индексы
            await self._add_to_indexes(fragment)
            
            logger.debug(f"Фрагмент {fragment.id} сохранен в Redis с TTL {ttl}с")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения фрагмента {fragment.id} в Redis: {e}")
            return False
    
    async def get_fragment(self, fragment_id: str) -> Optional[MemoryFragment]:
        """Получить фрагмент памяти из Redis"""
        try:
            fragment_key = f"{self.prefix}:fragments:{fragment_id}"
            fragment_data = await self.redis_client.get_key(fragment_key)
            
            if not fragment_data:
                return None
            
            data = json.loads(fragment_data)
            
            # Создаем объект MemoryFragment
            fragment = MemoryFragment(
                id=data["id"],
                content=data["content"],
                metadata=data["metadata"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                priority=data["priority"],
                fragment_type=data["fragment_type"],
                level=MemoryLevel(data["level"]),
                access_count=data["access_count"],
                last_accessed=datetime.fromisoformat(data["last_accessed"]) if data["last_accessed"] else None,
                created_at=datetime.fromisoformat(data["created_at"])
            )
            
            # Обновляем статистику доступа
            await self._update_access_stats(fragment)
            
            logger.debug(f"Фрагмент {fragment_id} получен из Redis")
            return fragment
            
        except Exception as e:
            logger.error(f"Ошибка получения фрагмента {fragment_id} из Redis: {e}")
            return None
    
    async def get_fragments_by_level(self, level: MemoryLevel, limit: int = 100) -> List[MemoryFragment]:
        """Получить фрагменты по уровню памяти"""
        try:
            level_key = f"{self.prefix}:level:{level.value}"
            fragment_ids = await self.redis_client.zrevrange(level_key, 0, limit - 1)
            
            fragments = []
            for fid in fragment_ids:
                fragment = await self.get_fragment(fid.decode() if isinstance(fid, bytes) else fid)
                if fragment:
                    fragments.append(fragment)
            
            logger.debug(f"Получено {len(fragments)} фрагментов уровня {level.value}")
            return fragments
            
        except Exception as e:
            logger.error(f"Ошибка получения фрагментов уровня {level.value}: {e}")
            return []
    
    async def get_fragments_by_priority(self, min_priority: float, limit: int = 100) -> List[MemoryFragment]:
        """Получить фрагменты по минимальному приоритету"""
        try:
            priority_key = f"{self.prefix}:priority"
            fragment_ids = await self.redis_client.zrangebyscore(
                priority_key, min_priority, float('inf'), 0, limit
            )
            
            fragments = []
            for fid in fragment_ids:
                fragment = await self.get_fragment(fid.decode() if isinstance(fid, bytes) else fid)
                if fragment:
                    fragments.append(fragment)
            
            logger.debug(f"Получено {len(fragments)} фрагментов с приоритетом >= {min_priority}")
            return fragments
            
        except Exception as e:
            logger.error(f"Ошибка получения фрагментов по приоритету: {e}")
            return []
    
    async def update_fragment(self, fragment: MemoryFragment) -> bool:
        """Обновить фрагмент памяти"""
        try:
            # Сначала удаляем старую версию из индексов
            await self._remove_from_indexes(fragment.id)
            
            # Затем сохраняем новую версию
            return await self.store_fragment(fragment)
            
        except Exception as e:
            logger.error(f"Ошибка обновления фрагмента {fragment.id}: {e}")
            return False
    
    async def delete_fragment(self, fragment_id: str) -> bool:
        """Удалить фрагмент памяти"""
        try:
            fragment_key = f"{self.prefix}:fragments:{fragment_id}"
            
            # Удаляем из индексов
            await self._remove_from_indexes(fragment_id)
            
            # Удаляем сам фрагмент
            await self.redis_client.delete_key(fragment_key)
            
            logger.debug(f"Фрагмент {fragment_id} удален из Redis")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления фрагмента {fragment_id}: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Получить статистику хранилища"""
        try:
            # Получаем количество фрагментов по уровням
            stats = {"level_counts": {}, "total_fragments": 0, "memory_usage": 0}
            
            for level in MemoryLevel:
                level_key = f"{self.prefix}:level:{level.value}"
                count = await self.redis_client.redis.zcard(level_key)
                stats["level_counts"][level.value] = count
                stats["total_fragments"] += count
            
            # Оценка использования памяти
            try:
                stats["memory_usage"] = await self.redis_client.estimate_memory_usage()
            except:
                stats["memory_usage"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики хранилища: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """Очистить просроченные фрагменты"""
        try:
            # Redis автоматически удаляет ключи с истекшим TTL
            # Но мы можем очистить индексы от несуществующих ключей
            
            cleaned_count = 0
            
            for level in MemoryLevel:
                level_key = f"{self.prefix}:level:{level.value}"
                fragment_ids = await self.redis_client.zrange(level_key, 0, batch_size)
                
                for fid in fragment_ids:
                    fragment_key = f"{self.prefix}:fragments:{fid}"
                    exists = await self.redis_client.redis.exists(fragment_key)
                    
                    if not exists:
                        # Удаляем из индексов
                        await self._remove_from_indexes(fid)
                        cleaned_count += 1
            
            logger.info(f"Очищено {cleaned_count} просроченных записей из индексов")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки просроченных фрагментов: {e}")
            return 0
    
    async def close(self):
        """Закрыть соединение с Redis"""
        try:
            await self.redis_client.close()
        except Exception as e:
            logger.error(f"Ошибка закрытия Redis соединения: {e}")
    
    # Приватные методы
    
    def _calculate_ttl(self, fragment: MemoryFragment) -> int:
        """Вычислить TTL для фрагмента на основе приоритета и уровня"""
        base_ttl = {
            MemoryLevel.L1: 3600,    # 1 час для L1
            MemoryLevel.L2: 86400,   # 1 день для L2  
            MemoryLevel.L3: 604800,  # 1 неделя для L3
            MemoryLevel.L4: 2592000  # 1 месяц для L4
        }
        
        ttl = base_ttl.get(fragment.level, 3600)
        
        # Модификатор на основе приоритета (0.5x - 2.0x)
        priority_modifier = max(0.5, min(2.0, fragment.priority))
        
        return int(ttl * priority_modifier)
    
    async def _add_to_indexes(self, fragment: MemoryFragment):
        """Добавить фрагмент в индексы"""
        try:
            # Индекс по уровню (сортированный по timestamp)
            level_key = f"{self.prefix}:level:{fragment.level.value}"
            await self.redis_client.zadd(level_key, {fragment.id: fragment.timestamp.timestamp()})
            
            # Индекс по приоритету
            priority_key = f"{self.prefix}:priority"
            await self.redis_client.zadd(priority_key, {fragment.id: fragment.priority})
            
            # Индекс по времени создания
            timeline_key = f"{self.prefix}:timeline"
            await self.redis_client.zadd(timeline_key, {fragment.id: fragment.created_at.timestamp()})
            
        except Exception as e:
            logger.error(f"Ошибка добавления в индексы: {e}")
    
    async def _remove_from_indexes(self, fragment_id: str):
        """Удалить фрагмент из всех индексов"""
        try:
            # Удаляем из всех индексов
            for level in MemoryLevel:
                level_key = f"{self.prefix}:level:{level.value}"
                await self.redis_client.zrem(level_key, fragment_id)
            
            priority_key = f"{self.prefix}:priority"
            await self.redis_client.zrem(priority_key, fragment_id)
            
            timeline_key = f"{self.prefix}:timeline"
            await self.redis_client.zrem(timeline_key, fragment_id)
            
        except Exception as e:
            logger.error(f"Ошибка удаления из индексов: {e}")
    
    async def _update_access_stats(self, fragment: MemoryFragment):
        """Обновить статистику доступа к фрагменту"""
        try:
            fragment.access_count += 1
            fragment.last_accessed = datetime.now()
            
            # Обновляем только статистику, не весь фрагмент
            fragment_key = f"{self.prefix}:fragments:{fragment.id}"
            
            # Получаем текущие данные
            current_data = await self.redis_client.get_key(fragment_key)
            if current_data:
                data = json.loads(current_data)
                data["access_count"] = fragment.access_count
                data["last_accessed"] = fragment.last_accessed.isoformat()
                
                # Пересохраняем с обновленным TTL
                ttl = self._calculate_ttl(fragment)
                await self.redis_client.set_key(
                    fragment_key,
                    json.dumps(data, ensure_ascii=False),
                    ttl
                )
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики доступа: {e}")


# ============================================================================
# ФАБРИКА ДЛЯ REDIS STORAGE
# ============================================================================

class RedisStorageFactory:
    """Фабрика для создания Redis хранилищ"""
    
    @staticmethod
    def create_memory_storage(redis_url: str = None, redis_db: int = 0) -> RedisMemoryStorage:
        """Создать Redis хранилище памяти"""
        return RedisMemoryStorage(redis_url, redis_db)


# ============================================================================
# КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ
# ============================================================================

def get_default_redis_config() -> Dict[str, Any]:
    """Получить конфигурацию Redis по умолчанию"""
    return {
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "redis_db": int(os.getenv("REDIS_DB", "0")),
        "prefix": "memory_cache:v3"
    }
