"""
MultiLevelMemoryStorage - объединяет все уровни хранения L1-L4 в единую систему.
Обеспечивает прозрачную работу с многоуровневой архитектурой памяти.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .interfaces import IMemoryStorage
from .models import MemoryFragment, MemoryLevel, MemoryStats
from .storage.redis_storage import RedisMemoryStorage
from .storage.sqlite_storage import SQLiteStorage
from .storage.chroma_storage import ChromaVectorStorage
from .storage.mock_cold_storage import MockColdStorage

logger = logging.getLogger(__name__)


class MultiLevelMemoryStorage(IMemoryStorage):
    """
    Многоуровневое хранилище памяти, объединяющее L1-L4.
    
    Архитектура:
    - L1 (Redis): Горячий кэш, TTL 1-24ч
    - L2 (SQLite): Теплое хранилище, TTL 1-7д
    - L3 (ChromaDB): Векторный индекс, TTL 1-30д
    - L4 (S3/Mock): Холодный архив, бесконечный TTL
    """
    
    def __init__(self):
        # Хранилища для каждого уровня
        self.storages: Dict[MemoryLevel, IMemoryStorage] = {}
        
        # Статистика
        self.stats = {
            "total_operations": 0,
            "operations_by_level": {level: 0 for level in MemoryLevel},
            "last_operation_time": None,
            "initialization_time": datetime.now()
        }
        
        # Маршрутизация операций по уровням
        self.level_routing = {
            MemoryLevel.L1: "hot_cache",
            MemoryLevel.L2: "warm_storage", 
            MemoryLevel.L3: "vector_index",
            MemoryLevel.L4: "cold_archive"
        }
        
        logger.info("MultiLevelMemoryStorage created")
    
    async def init_storage(self) -> bool:
        """Инициализирует все уровни хранения"""
        try:
            # L1: Redis (горячий кэш)
            try:
                l1_storage = RedisMemoryStorage()
                if await l1_storage.init_storage():
                    self.storages[MemoryLevel.L1] = l1_storage
                    logger.info("L1 (Redis) storage initialized")
                else:
                    logger.warning("Failed to initialize L1 (Redis) storage")
            except Exception as e:
                logger.error(f"Error initializing L1 storage: {e}")
            
            # L2: SQLite (теплое хранилище)
            try:
                l2_storage = SQLiteStorage()
                if await l2_storage.init_storage():
                    self.storages[MemoryLevel.L2] = l2_storage
                    logger.info("L2 (SQLite) storage initialized")
                else:
                    logger.warning("Failed to initialize L2 (SQLite) storage")
            except Exception as e:
                logger.error(f"Error initializing L2 storage: {e}")
            
            # L3: ChromaDB (векторный индекс)
            try:
                l3_storage = ChromaVectorStorage()
                if await l3_storage.init_storage():
                    self.storages[MemoryLevel.L3] = l3_storage
                    logger.info("L3 (ChromaDB) storage initialized")
                else:
                    logger.warning("Failed to initialize L3 (ChromaDB) storage")
            except Exception as e:
                logger.error(f"Error initializing L3 storage: {e}")
            
            # L4: Mock Cold Storage (холодный архив)
            try:
                l4_storage = MockColdStorage()
                if await l4_storage.init_storage():
                    self.storages[MemoryLevel.L4] = l4_storage
                    logger.info("L4 (Mock Cold) storage initialized")
                else:
                    logger.warning("Failed to initialize L4 (Mock Cold) storage")
            except Exception as e:
                logger.error(f"Error initializing L4 storage: {e}")
            
            # Проверяем, что хотя бы один уровень инициализирован
            if not self.storages:
                logger.error("No storage levels initialized successfully")
                return False
            
            logger.info(f"MultiLevelMemoryStorage initialized with {len(self.storages)} levels: {list(self.storages.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing multi-level storage: {e}")
            return False
    
    async def store_fragment(self, fragment: MemoryFragment, level: Optional[MemoryLevel] = None) -> bool:
        """
        Сохраняет фрагмент на указанном уровне или автоматически определяет уровень
        
        Args:
            fragment: Фрагмент для сохранения
            level: Целевой уровень (если None, определяется автоматически)
            
        Returns:
            True если успешно сохранен
        """
        try:
            # Автоматическое определение уровня, если не указан
            if level is None:
                level = self._determine_optimal_level(fragment)
            
            # Получаем хранилище для уровня
            storage = self.storages.get(level)
            if not storage:
                logger.warning(f"Storage for level {level} not available")
                # Пробуем сохранить на доступном уровне
                for fallback_level, fallback_storage in self.storages.items():
                    if await fallback_storage.store_fragment(fragment, fallback_level):
                        fragment.level = fallback_level
                        self._update_stats("store_fragment", fallback_level)
                        logger.info(f"Fragment {fragment.id} stored on fallback level {fallback_level}")
                        return True
                return False
            
            # Устанавливаем уровень в фрагменте
            fragment.level = level
            
            # Сохраняем фрагмент
            success = await storage.store_fragment(fragment, level)
            
            if success:
                self._update_stats("store_fragment", level)
                logger.debug(f"Fragment {fragment.id} stored on level {level}")
            else:
                logger.warning(f"Failed to store fragment {fragment.id} on level {level}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing fragment: {e}")
            return False
    
    def _determine_optimal_level(self, fragment: MemoryFragment) -> MemoryLevel:
        """Автоматически определяет оптимальный уровень для фрагмента"""
        
        # Высокий приоритет → L1 (горячий кэш)
        if fragment.priority >= 0.8:
            return MemoryLevel.L1
        
        # Средний приоритет → L2 (теплое хранилище)
        elif fragment.priority >= 0.5:
            return MemoryLevel.L2
        
        # Низкий приоритет, но есть векторизуемый контент → L3
        elif fragment.priority >= 0.2 and fragment.content and len(fragment.content) > 50:
            return MemoryLevel.L3
        
        # Очень низкий приоритет или архивные данные → L4
        else:
            return MemoryLevel.L4
    
    async def get_fragment(self, fragment_id: str, level: Optional[MemoryLevel] = None) -> Optional[MemoryFragment]:
        """
        Получает фрагмент по ID
        
        Args:
            fragment_id: ID фрагмента
            level: Конкретный уровень для поиска (если None, ищет на всех уровнях)
            
        Returns:
            Найденный фрагмент или None
        """
        try:
            # Если указан конкретный уровень
            if level is not None:
                storage = self.storages.get(level)
                if storage:
                    fragment = await storage.get_fragment(fragment_id, level)
                    if fragment:
                        self._update_stats("get_fragment", level)
                        return fragment
                return None
            
            # Поиск на всех уровнях (начинаем с горячих)
            search_order = [MemoryLevel.L1, MemoryLevel.L2, MemoryLevel.L3, MemoryLevel.L4]
            
            for search_level in search_order:
                storage = self.storages.get(search_level)
                if storage:
                    fragment = await storage.get_fragment(fragment_id, search_level)
                    if fragment:
                        self._update_stats("get_fragment", search_level)
                        logger.debug(f"Fragment {fragment_id} found on level {search_level}")
                        return fragment
            
            logger.debug(f"Fragment {fragment_id} not found on any level")
            return None
            
        except Exception as e:
            logger.error(f"Error getting fragment {fragment_id}: {e}")
            return None
    
    async def update_fragment(self, fragment: MemoryFragment, level: Optional[MemoryLevel] = None) -> bool:
        """Обновляет фрагмент"""
        try:
            # Определяем уровень
            target_level = level or fragment.level
            
            storage = self.storages.get(target_level)
            if not storage:
                logger.warning(f"Storage for level {target_level} not available")
                return False
            
            success = await storage.update_fragment(fragment, target_level)
            
            if success:
                self._update_stats("update_fragment", target_level)
                logger.debug(f"Fragment {fragment.id} updated on level {target_level}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating fragment: {e}")
            return False
    
    async def delete_fragment(self, fragment_id: str, level: Optional[MemoryLevel] = None) -> bool:
        """Удаляет фрагмент"""
        try:
            # Если указан конкретный уровень
            if level is not None:
                storage = self.storages.get(level)
                if storage:
                    success = await storage.delete_fragment(fragment_id, level)
                    if success:
                        self._update_stats("delete_fragment", level)
                        logger.debug(f"Fragment {fragment_id} deleted from level {level}")
                    return success
                return False
            
            # Удаляем со всех уровней
            deleted_any = False
            for del_level, storage in self.storages.items():
                try:
                    if await storage.delete_fragment(fragment_id, del_level):
                        deleted_any = True
                        self._update_stats("delete_fragment", del_level)
                        logger.debug(f"Fragment {fragment_id} deleted from level {del_level}")
                except Exception as e:
                    logger.warning(f"Error deleting from level {del_level}: {e}")
            
            return deleted_any
            
        except Exception as e:
            logger.error(f"Error deleting fragment {fragment_id}: {e}")
            return False
    
    async def get_fragments_by_level(self, level: MemoryLevel, limit: Optional[int] = None) -> List[MemoryFragment]:
        """Получает фрагменты с указанного уровня"""
        try:
            storage = self.storages.get(level)
            if not storage:
                logger.warning(f"Storage for level {level} not available")
                return []
            
            fragments = await storage.get_fragments_by_level(level, limit)
            self._update_stats("get_fragments_by_level", level)
            
            return fragments
            
        except Exception as e:
            logger.error(f"Error getting fragments from level {level}: {e}")
            return []
    
    async def get_fragments_by_priority(self, min_priority: float, max_priority: float = 1.0,
                                       limit: Optional[int] = None) -> List[MemoryFragment]:
        """Получает фрагменты по диапазону приоритета"""
        try:
            all_fragments = []
            
            # Собираем фрагменты со всех уровней
            for level, storage in self.storages.items():
                try:
                    level_fragments = await storage.get_fragments_by_priority(
                        min_priority, max_priority, limit
                    )
                    all_fragments.extend(level_fragments)
                    self._update_stats("get_fragments_by_priority", level)
                except Exception as e:
                    logger.warning(f"Error getting fragments by priority from level {level}: {e}")
            
            # Сортируем по приоритету
            all_fragments.sort(key=lambda f: f.priority, reverse=True)
            
            # Применяем лимит
            if limit:
                all_fragments = all_fragments[:limit]
            
            return all_fragments
            
        except Exception as e:
            logger.error(f"Error getting fragments by priority: {e}")
            return []
    
    async def search_fragments(self, query: str, limit: int = 10) -> List[MemoryFragment]:
        """Поиск фрагментов по запросу"""
        try:
            all_results = []
            
            # Поиск на каждом уровне
            for level, storage in self.storages.items():
                try:
                    level_results = await storage.search_fragments(query, limit)
                    all_results.extend(level_results)
                    self._update_stats("search_fragments", level)
                except Exception as e:
                    logger.warning(f"Error searching on level {level}: {e}")
            
            # Убираем дубликаты по ID
            seen_ids = set()
            unique_results = []
            for fragment in all_results:
                if fragment.id not in seen_ids:
                    unique_results.append(fragment)
                    seen_ids.add(fragment.id)
            
            # Сортируем по релевантности (приоритет + свежесть)
            unique_results.sort(
                key=lambda f: (f.priority, f.timestamp), 
                reverse=True
            )
            
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching fragments: {e}")
            return []
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Получает общую статистику хранилища"""
        try:
            overall_stats = {
                "multi_level_stats": self.stats.copy(),
                "level_stats": {},
                "summary": {
                    "total_levels": len(self.storages),
                    "active_levels": list(self.storages.keys()),
                    "total_fragments": 0,
                    "total_size_bytes": 0
                }
            }
            
            # Собираем статистику с каждого уровня
            for level, storage in self.storages.items():
                try:
                    level_stats = await storage.get_storage_stats()
                    overall_stats["level_stats"][level.value] = level_stats
                    
                    # Суммируем общую статистику
                    if isinstance(level_stats, dict):
                        overall_stats["summary"]["total_fragments"] += level_stats.get("fragment_count", 0)
                        overall_stats["summary"]["total_size_bytes"] += level_stats.get("total_size_bytes", 0)
                        
                except Exception as e:
                    logger.warning(f"Error getting stats from level {level}: {e}")
                    overall_stats["level_stats"][level.value] = {"error": str(e)}
            
            return overall_stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}
    
    async def get_level_statistics(self, level: MemoryLevel) -> Optional[Dict[str, Any]]:
        """Получает статистику конкретного уровня"""
        try:
            storage = self.storages.get(level)
            if not storage:
                return None
            
            return await storage.get_level_statistics(level)
            
        except Exception as e:
            logger.error(f"Error getting level statistics: {e}")
            return None
    
    def get_storage_for_level(self, level: Union[MemoryLevel, str]) -> Optional[IMemoryStorage]:
        """Получает хранилище для конкретного уровня"""
        if isinstance(level, str):
            # Преобразуем строку в MemoryLevel
            level_map = {
                "L1": MemoryLevel.L1,
                "L2": MemoryLevel.L2, 
                "L3": MemoryLevel.L3,
                "L4": MemoryLevel.L4
            }
            level = level_map.get(level)
        
        return self.storages.get(level) if level else None
    
    def _update_stats(self, operation: str, level: MemoryLevel):
        """Обновляет статистику операций"""
        self.stats["total_operations"] += 1
        self.stats["operations_by_level"][level] += 1
        self.stats["last_operation_time"] = datetime.now()
    
    async def migrate_fragment(self, fragment_id: str, from_level: MemoryLevel, 
                              to_level: MemoryLevel) -> bool:
        """
        Перемещает фрагмент между уровнями
        
        Args:
            fragment_id: ID фрагмента
            from_level: Исходный уровень
            to_level: Целевой уровень
            
        Returns:
            True если успешно перемещен
        """
        try:
            # Получаем фрагмент с исходного уровня
            fragment = await self.get_fragment(fragment_id, from_level)
            if not fragment:
                logger.warning(f"Fragment {fragment_id} not found on level {from_level}")
                return False
            
            # Сохраняем на целевом уровне
            fragment.level = to_level
            if not await self.store_fragment(fragment, to_level):
                logger.error(f"Failed to store fragment {fragment_id} on level {to_level}")
                return False
            
            # Удаляем с исходного уровня
            if not await self.delete_fragment(fragment_id, from_level):
                logger.warning(f"Failed to delete fragment {fragment_id} from level {from_level}")
                # Не возвращаем False, так как фрагмент уже сохранен на новом уровне
            
            logger.info(f"Fragment {fragment_id} migrated from {from_level} to {to_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating fragment {fragment_id}: {e}")
            return False
    
    async def batch_migrate(self, migrations: List[Tuple[str, MemoryLevel, MemoryLevel]]) -> Dict[str, Any]:
        """
        Пакетное перемещение фрагментов
        
        Args:
            migrations: Список (fragment_id, from_level, to_level)
            
        Returns:
            Результат пакетного перемещения
        """
        try:
            successful = 0
            failed = 0
            results = []
            
            for fragment_id, from_level, to_level in migrations:
                try:
                    if await self.migrate_fragment(fragment_id, from_level, to_level):
                        successful += 1
                        results.append({
                            "fragment_id": fragment_id,
                            "from_level": from_level.value,
                            "to_level": to_level.value,
                            "status": "success"
                        })
                    else:
                        failed += 1
                        results.append({
                            "fragment_id": fragment_id,
                            "from_level": from_level.value,
                            "to_level": to_level.value,
                            "status": "failed"
                        })
                except Exception as e:
                    failed += 1
                    results.append({
                        "fragment_id": fragment_id,
                        "from_level": from_level.value if from_level else None,
                        "to_level": to_level.value if to_level else None,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "total_migrations": len(migrations),
                "successful": successful,
                "failed": failed,
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Error in batch migration: {e}")
            return {"error": str(e)}
    
    async def cleanup_all_levels(self) -> Dict[str, Any]:
        """Запускает очистку на всех уровнях"""
        try:
            cleanup_results = {}
            
            for level, storage in self.storages.items():
                try:
                    # Пробуем вызвать cleanup, если он есть
                    if hasattr(storage, 'cleanup'):
                        result = await storage.cleanup()
                        cleanup_results[level.value] = result
                    else:
                        cleanup_results[level.value] = {"status": "not_supported"}
                        
                except Exception as e:
                    logger.error(f"Error cleaning up level {level}: {e}")
                    cleanup_results[level.value] = {"status": "error", "error": str(e)}
            
            return {
                "cleanup_results": cleanup_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup all levels: {e}")
            return {"error": str(e)}
