"""
Главный контроллер системы памяти как кэш-системы.
Координирует работу Promoter, Demoter и Evictor для автоматического управления данными.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import (
    MemoryFragment, MemoryLevel, FragmentType, MemoryConfig, 
    MemoryStats, AccessPattern, ActivityScore
)
from .interfaces import (
    IDataPromoter, IDataDemoter, IDataEvictor, 
    IMemoryAnalyzer, IMemoryOptimizer, IMemoryMonitor, IMemoryStorage
)

# Импорты для storage компонентов
try:
    from ..storage.redis_storage import RedisMemoryStorage
except ImportError:
    RedisMemoryStorage = None

try:
    from ..storage.chroma_storage import ChromaVectorStorage
except ImportError:
    ChromaVectorStorage = None

try:
    from ..storage.sqlite_storage import SQLiteStorage
    from ..storage.base import StorageConfig
except ImportError:
    SQLiteStorage = None
    StorageConfig = None

try:
    from ..storage.mock_cold_storage import MockColdStorage
except ImportError:
    MockColdStorage = None

logger = logging.getLogger(__name__)


class MemoryController:
    """
    Главный координатор управления памятью между уровнями.
    
    Отвечает за:
    - Обработку новых фрагментов
    - Координацию между компонентами
    - Мониторинг состояния памяти
    - Автоматическую оптимизацию
    """
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.is_running = False
        
        # Компоненты системы
        self.promoter: Optional[IDataPromoter] = None
        self.demoter: Optional[IDataDemoter] = None
        self.evictor: Optional[IDataEvictor] = None
        self.analyzer: Optional[IMemoryAnalyzer] = None
        self.optimizer: Optional[IMemoryOptimizer] = None
        self.monitor: Optional[IMemoryMonitor] = None
        self.storage: Optional[IMemoryStorage] = None
        
        # Фоновые задачи
        self._optimization_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Статистика
        self.stats = MemoryStats()
        self.last_optimization = datetime.utcnow()
        self.last_cleanup = datetime.utcnow()
        
        logger.info("MemoryController инициализирован")
    
    async def initialize(self) -> bool:
        """Инициализация контроллера и всех компонентов"""
        try:
            logger.info("Инициализация MemoryController...")
            
            # Сначала инициализируем storage компоненты
            await self._init_storage_components()
            
            # Инициализируем остальные компоненты если они доступны
            if self.promoter:
                await self.promoter.initialize()
            if self.demoter:
                await self.demoter.initialize()
            if self.evictor:
                await self.evictor.initialize()
            if self.analyzer:
                await self.analyzer.initialize()
            if self.optimizer:
                await self.optimizer.initialize()
            if self.monitor:
                await self.monitor.initialize()
            if self.storage:
                await self.storage.initialize()
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("MemoryController успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации MemoryController: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Завершение работы контроллера"""
        try:
            logger.info("Завершение работы MemoryController...")
            
            self.is_running = False
            
            # Останавливаем фоновые задачи
            await self._stop_background_tasks()
            
            # Завершаем компоненты
            if self.promoter:
                await self.promoter.shutdown()
            if self.demoter:
                await self.demoter.shutdown()
            if self.evictor:
                await self.evictor.shutdown()
            if self.analyzer:
                await self.analyzer.shutdown()
            if self.optimizer:
                await self.optimizer.initialize()
            if self.monitor:
                await self.monitor.shutdown()
            if self.storage:
                await self.storage.shutdown()
            
            logger.info("MemoryController успешно завершил работу")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка завершения работы MemoryController: {e}")
            return False
    
    async def process_fragment(self, fragment: MemoryFragment) -> bool:
        """
        Обработка нового фрагмента с автоматическим размещением.
        
        Процесс:
        1. Определяем начальный уровень
        2. Размещаем на начальном уровне
        3. Запускаем фоновую оптимизацию
        """
        try:
            logger.debug(f"Обработка нового фрагмента: {fragment.id}")
            
            # 1. Определяем начальный уровень
            initial_level = self._determine_initial_level(fragment)
            fragment.current_level = initial_level
            
            # 2. Размещаем на начальном уровне
            if self.storage:
                success = await self.storage.store_fragment(fragment, initial_level)
                if not success:
                    logger.error(f"Не удалось сохранить фрагмент {fragment.id} на уровне {initial_level}")
                    return False
            
            # 3. Обновляем статистику
            await self._update_stats_on_fragment_add(fragment, initial_level)
            
            # 4. Запускаем фоновую оптимизацию
            asyncio.create_task(self._optimize_memory_layout())
            
            logger.debug(f"Фрагмент {fragment.id} успешно обработан и размещен на уровне {initial_level}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки фрагмента {fragment.id}: {e}")
            return False
    
    def _determine_initial_level(self, fragment: MemoryFragment) -> MemoryLevel:
        """Определяет начальный уровень для фрагмента"""
        if fragment.priority >= 0.8:
            return MemoryLevel.L1_HOT  # Высокий приоритет → горячий кэш
        elif fragment.priority >= 0.5:
            return MemoryLevel.L2_WARM  # Средний приоритет → теплое хранилище
        else:
            return MemoryLevel.L3_VECTOR  # Низкий приоритет → векторное хранилище
    
    async def _optimize_memory_layout(self):
        """Фоновая оптимизация распределения памяти"""
        try:
            if not self.is_running:
                return
            
            logger.debug("Запуск фоновой оптимизации памяти...")
            
            # 1. Анализируем и продвигаем данные
            if self.promoter:
                await self._run_promotion_cycle()
            
            # 2. Анализируем и понижаем данные
            if self.demoter:
                await self._run_demotion_cycle()
            
            # 3. Очищаем устаревшие данные
            if self.evictor:
                await self._run_eviction_cycle()
            
            # 4. Оптимизируем общее распределение
            if self.optimizer:
                await self.optimizer.optimize_level_distribution()
            
            self.last_optimization = datetime.utcnow()
            logger.debug("Фоновая оптимизация памяти завершена")
            
        except Exception as e:
            logger.error(f"Ошибка фоновой оптимизации памяти: {e}")
    
    async def _run_promotion_cycle(self):
        """Выполняет цикл продвижения данных"""
        try:
            # Анализируем кандидатов для продвижения с L3
            if self.promoter:
                l3_candidates = await self.promoter.analyze_promotion_candidates(MemoryLevel.L3_VECTOR)
                if l3_candidates:
                    await self.promoter.batch_promote(l3_candidates)
                
                # Анализируем кандидатов для продвижения с L2
                l2_candidates = await self.promoter.analyze_promotion_candidates(MemoryLevel.L2_WARM)
                if l2_candidates:
                    await self.promoter.batch_promote(l2_candidates)
                    
        except Exception as e:
            logger.error(f"Ошибка цикла продвижения: {e}")
    
    async def _run_demotion_cycle(self):
        """Выполняет цикл понижения данных"""
        try:
            # Анализируем кандидатов для понижения с L1
            if self.demoter:
                l1_candidates = await self.demoter.analyze_demotion_candidates(MemoryLevel.L1_HOT)
                if l1_candidates:
                    await self.demoter.batch_demote(l1_candidates)
                
                # Анализируем кандидатов для понижения с L2
                l2_candidates = await self.demoter.analyze_demotion_candidates(MemoryLevel.L2_WARM)
                if l2_candidates:
                    await self.demoter.batch_demote(l2_candidates)
                    
        except Exception as e:
            logger.error(f"Ошибка цикла понижения: {e}")
    
    async def _run_eviction_cycle(self):
        """Выполняет цикл очистки данных"""
        try:
            # Очищаем просроченные данные по всем уровням
            if self.evictor:
                for level in [MemoryLevel.L1_HOT, MemoryLevel.L2_WARM, MemoryLevel.L3_VECTOR]:
                    expired_fragments = await self.evictor.find_expired_fragments(level)
                    if expired_fragments:
                        await self.evictor.batch_evict(expired_fragments)
                        
        except Exception as e:
            logger.error(f"Ошибка цикла очистки: {e}")
    
    async def _update_stats_on_fragment_add(self, fragment: MemoryFragment, level: MemoryLevel):
        """Обновляет статистику при добавлении фрагмента"""
        try:
            if level == MemoryLevel.L1_HOT:
                self.stats.l1_count += 1
            elif level == MemoryLevel.L2_WARM:
                self.stats.l2_count += 1
            elif level == MemoryLevel.L3_VECTOR:
                self.stats.l3_count += 1
            elif level == MemoryLevel.L4_COLD:
                self.stats.l4_count += 1
                
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
    
    async def _start_background_tasks(self):
        """Запускает фоновые задачи"""
        try:
            # Задача оптимизации
            self._optimization_task = asyncio.create_task(
                self._optimization_loop()
            )
            
            # Задача очистки
            self._cleanup_task = asyncio.create_task(
                self._cleanup_loop()
            )
            
            # Задача мониторинга
            self._monitoring_task = asyncio.create_task(
                self._monitoring_loop()
            )
            
            logger.info("Фоновые задачи запущены")
            
        except Exception as e:
            logger.error(f"Ошибка запуска фоновых задач: {e}")
    
    async def _stop_background_tasks(self):
        """Останавливает фоновые задачи"""
        try:
            if self._optimization_task:
                self._optimization_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._monitoring_task:
                self._monitoring_task.cancel()
                
            logger.info("Фоновые задачи остановлены")
            
        except Exception as e:
            logger.error(f"Ошибка остановки фоновых задач: {e}")
    
    async def _optimization_loop(self):
        """Цикл оптимизации памяти"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.optimization_interval)
                if self.is_running:
                    await self._optimize_memory_layout()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле оптимизации: {e}")
    
    async def _cleanup_loop(self):
        """Цикл очистки памяти"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                if self.is_running:
                    await self._run_eviction_cycle()
                    self.last_cleanup = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле очистки: {e}")
    
    async def _monitoring_loop(self):
        """Цикл мониторинга памяти"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                if self.is_running:
                    await self._update_monitoring_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
    
    async def _update_monitoring_stats(self):
        """Обновляет статистику мониторинга"""
        try:
            if self.monitor:
                self.stats = await self.monitor.get_memory_stats()
                
        except Exception as e:
            logger.error(f"Ошибка обновления статистики мониторинга: {e}")
    
    async def _init_storage_components(self):
        """Инициализация storage компонентов для разных уровней"""
        try:
            # Создаем мультиуровневое хранилище
            self.storage = MultiLevelMemoryStorage()
            
            # L1: Redis (Hot Cache)
            if RedisMemoryStorage:
                try:
                    redis_storage = RedisMemoryStorage()
                    if await redis_storage.init_storage():
                        self.storage.add_level_storage(MemoryLevel.L1, redis_storage)
                        logger.info("L1 Redis хранилище инициализировано")
                    else:
                        logger.warning("Не удалось инициализировать L1 Redis хранилище")
                except Exception as e:
                    logger.warning(f"Ошибка инициализации Redis: {e}")
            
            # L2: SQLite (Warm Storage) - пока используем заглушку
            logger.info("L2 SQLite хранилище (заглушка - планируется интеграция)")
            
            # L3: ChromaDB (Vector Storage) - пока используем заглушку  
            logger.info("L3 ChromaDB хранилище (заглушка - планируется интеграция)")
            
            # L4: Cold Archive (Mock Storage)
            if MockColdStorage:
                try:
                    cold_storage = MockColdStorage()
                    if await cold_storage.init_storage():
                        self.storage.add_level_storage(MemoryLevel.L4, cold_storage)
                        logger.info("L4 Cold Archive хранилище инициализировано (заглушка)")
                    else:
                        logger.warning("Не удалось инициализировать L4 Cold Archive хранилище")
                except Exception as e:
                    logger.warning(f"Ошибка инициализации Cold Archive: {e}")
            
            logger.info("Storage компоненты инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации storage компонентов: {e}")
            # Fallback на mock storage
            self.storage = MockMemoryStorage()
    
    # Методы для установки компонентов
    def set_promoter(self, promoter: IDataPromoter):
        """Устанавливает компонент продвижения данных"""
        self.promoter = promoter
        logger.info("DataPromoter установлен")
    
    def set_demoter(self, demoter: IDataDemoter):
        """Устанавливает компонент понижения данных"""
        self.demoter = demoter
        logger.info("DataDemoter установлен")
    
    def set_evictor(self, evictor: IDataEvictor):
        """Устанавливает компонент очистки данных"""
        self.evictor = evictor
        logger.info("DataEvictor установлен")
    
    def set_analyzer(self, analyzer: IMemoryAnalyzer):
        """Устанавливает компонент анализа памяти"""
        self.analyzer = analyzer
        logger.info("MemoryAnalyzer установлен")
    
    def set_optimizer(self, optimizer: IMemoryOptimizer):
        """Устанавливает компонент оптимизации памяти"""
        self.optimizer = optimizer
        logger.info("MemoryOptimizer установлен")
    
    def set_monitor(self, monitor: IMemoryMonitor):
        """Устанавливает компонент мониторинга памяти"""
        self.monitor = monitor
        logger.info("MemoryMonitor установлен")
    
    def set_storage(self, storage: IMemoryStorage):
        """Устанавливает компонент хранилища"""
        self.storage = storage
        logger.info("MemoryStorage установлен")
    
    # Методы для получения информации
    async def get_status(self) -> Dict[str, Any]:
        """Получает текущий статус контроллера"""
        return {
            "is_running": self.is_running,
            "last_optimization": self.last_optimization.isoformat() if self.last_optimization else None,
            "last_cleanup": self.last_cleanup.isoformat() if self.last_cleanup else None,
            "components": {
                "promoter": self.promoter is not None,
                "demoter": self.demoter is not None,
                "evictor": self.evictor is not None,
                "analyzer": self.analyzer is not None,
                "optimizer": self.optimizer is not None,
                "monitor": self.monitor is not None,
                "storage": self.storage is not None,
            }
        }
    
    async def get_stats(self) -> MemoryStats:
        """Получает статистику системы памяти"""
        return self.stats


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ
# ============================================================================

class MultiLevelMemoryStorage(IMemoryStorage):
    """Мультиуровневое хранилище, объединяющее разные storage компоненты"""
    
    def __init__(self):
        self.level_storages: Dict[MemoryLevel, IMemoryStorage] = {}
    
    def add_level_storage(self, level: MemoryLevel, storage: IMemoryStorage):
        """Добавить хранилище для уровня"""
        self.level_storages[level] = storage
    
    async def initialize(self) -> bool:
        """Инициализация всех уровней хранилища"""
        for level, storage in self.level_storages.items():
            try:
                if hasattr(storage, 'init_storage'):
                    await storage.init_storage()
                elif hasattr(storage, 'initialize'):
                    await storage.initialize()
            except Exception as e:
                logger.error(f"Ошибка инициализации storage уровня {level}: {e}")
        return True
    
    async def store_fragment(self, fragment: MemoryFragment) -> bool:
        """Сохранить фрагмент на соответствующем уровне"""
        storage = self.level_storages.get(fragment.level)
        if storage:
            return await storage.store_fragment(fragment)
        else:
            logger.warning(f"Нет storage для уровня {fragment.level}")
            return False
    
    async def get_fragment(self, fragment_id: str, level: MemoryLevel = None) -> Optional[MemoryFragment]:
        """Получить фрагмент с указанного уровня или поиск по всем уровням"""
        if level and level in self.level_storages:
            return await self.level_storages[level].get_fragment(fragment_id)
        
        # Поиск по всем уровням
        for storage in self.level_storages.values():
            fragment = await storage.get_fragment(fragment_id)
            if fragment:
                return fragment
        return None
    
    async def get_fragments_by_level(self, level: MemoryLevel, limit: int = 100) -> List[MemoryFragment]:
        """Получить фрагменты с указанного уровня"""
        storage = self.level_storages.get(level)
        if storage:
            return await storage.get_fragments_by_level(level, limit)
        return []
    
    async def get_fragments_by_priority(self, min_priority: float, limit: int = 100) -> List[MemoryFragment]:
        """Получить фрагменты по приоритету со всех уровней"""
        all_fragments = []
        for storage in self.level_storages.values():
            fragments = await storage.get_fragments_by_priority(min_priority, limit)
            all_fragments.extend(fragments)
        
        # Сортируем по приоритету и ограничиваем
        all_fragments.sort(key=lambda x: x.priority, reverse=True)
        return all_fragments[:limit]
    
    async def update_fragment(self, fragment: MemoryFragment) -> bool:
        """Обновить фрагмент на соответствующем уровне"""
        storage = self.level_storages.get(fragment.level)
        if storage:
            return await storage.update_fragment(fragment)
        return False
    
    async def delete_fragment(self, fragment_id: str, level: MemoryLevel = None) -> bool:
        """Удалить фрагмент с указанного уровня или со всех уровней"""
        if level and level in self.level_storages:
            return await self.level_storages[level].delete_fragment(fragment_id)
        
        # Удаление со всех уровней
        success = False
        for storage in self.level_storages.values():
            if await storage.delete_fragment(fragment_id):
                success = True
        return success
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Получить статистику всех уровней хранилища"""
        stats = {"levels": {}, "total": {"fragments": 0, "memory": 0}}
        
        for level, storage in self.level_storages.items():
            level_stats = await storage.get_storage_stats()
            stats["levels"][level.value] = level_stats
            
            if "total_fragments" in level_stats:
                stats["total"]["fragments"] += level_stats["total_fragments"]
            if "memory_usage" in level_stats:
                stats["total"]["memory"] += level_stats["memory_usage"]
        
        return stats
    
    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """Очистить просроченные фрагменты на всех уровнях"""
        total_cleaned = 0
        for storage in self.level_storages.values():
            cleaned = await storage.cleanup_expired(batch_size)
            total_cleaned += cleaned
        return total_cleaned
