"""
Интеграция всех компонентов памяти в единый контроллер.
Расширяет базовый MemoryController новой функциональностью.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .controller import MemoryController
from .promoter import DataPromoter
from .demoter import DataDemoter
from .evictor import DataEvictor
from .multi_level_storage import MultiLevelMemoryStorage
from .models import MemoryFragment, MemoryLevel, MemoryConfig

logger = logging.getLogger(__name__)


class EnhancedMemoryController(MemoryController):
    """
    Расширенный контроллер памяти с полной реализацией всех компонентов.
    
    Дополнительные возможности:
    - Многоуровневое хранилище L1-L4
    - Автоматическое продвижение данных (DataPromoter)
    - Автоматическое понижение данных (DataDemoter)
    - Автоматическое удаление данных (DataEvictor)
    - Интегрированная статистика и мониторинг
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        # Расширенные компоненты
        self.multi_storage: Optional[MultiLevelMemoryStorage] = None
        self.data_promoter: Optional[DataPromoter] = None
        self.data_demoter: Optional[DataDemoter] = None
        self.data_evictor: Optional[DataEvictor] = None
        
        # Расширенная статистика
        self.enhanced_stats = {
            "total_fragments_processed": 0,
            "promotions_executed": 0,
            "demotions_executed": 0,
            "evictions_executed": 0,
            "last_full_cycle": None,
            "cycle_performance": []
        }
        
        logger.info("EnhancedMemoryController initialized")
    
    async def initialize(self) -> bool:
        """Инициализирует все компоненты расширенного контроллера"""
        try:
            # 1. Инициализируем многоуровневое хранилище
            self.multi_storage = MultiLevelMemoryStorage()
            if not await self.multi_storage.init_storage():
                logger.error("Failed to initialize multi-level storage")
                return False
            
            # Устанавливаем хранилище в базовом контроллере
            self.storage = self.multi_storage
            
            # 2. Инициализируем компоненты управления данными
            self.data_promoter = DataPromoter(self.multi_storage, self.config)
            self.data_demoter = DataDemoter(self.multi_storage, self.config)
            self.data_evictor = DataEvictor(self.multi_storage, self.config)
            
            # Устанавливаем компоненты в базовом контроллере
            self.promoter = self.data_promoter
            self.demoter = self.data_demoter
            self.evictor = self.data_evictor
            
            # 3. Запускаем базовую инициализацию
            if not await super().initialize():
                logger.error("Failed to initialize base controller")
                return False
            
            logger.info("EnhancedMemoryController fully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing enhanced controller: {e}")
            return False
    
    async def process_fragment_enhanced(self, fragment: MemoryFragment) -> MemoryFragment:
        """
        Расширенная обработка фрагмента с автоматическим определением уровня
        
        Args:
            fragment: Фрагмент для обработки
            
        Returns:
            Обработанный фрагмент
        """
        try:
            # Базовая обработка
            processed_fragment = await self.process_fragment(fragment)
            
            # Автоматическое определение оптимального уровня
            if not processed_fragment.level:
                optimal_level = self._determine_optimal_level(processed_fragment)
                processed_fragment.level = optimal_level
            
            # Сохранение на определенном уровне
            if self.multi_storage:
                await self.multi_storage.store_fragment(processed_fragment, processed_fragment.level)
            
            # Обновляем расширенную статистику
            self.enhanced_stats["total_fragments_processed"] += 1
            
            logger.debug(f"Enhanced processing completed for fragment {fragment.id} on level {processed_fragment.level}")
            
            return processed_fragment
            
        except Exception as e:
            logger.error(f"Error in enhanced fragment processing: {e}")
            return fragment
    
    def _determine_optimal_level(self, fragment: MemoryFragment) -> MemoryLevel:
        """Определяет оптимальный уровень для фрагмента"""
        
        # Высокий приоритет и недавний доступ → L1
        if fragment.priority >= 0.8 and fragment.access_count > 0:
            return MemoryLevel.L1
        
        # Средний приоритет или активность → L2
        elif fragment.priority >= 0.5 or fragment.access_count >= 3:
            return MemoryLevel.L2
        
        # Есть контент для векторизации → L3
        elif fragment.content and len(fragment.content) > 100:
            return MemoryLevel.L3
        
        # Низкий приоритет или архивные данные → L4
        else:
            return MemoryLevel.L4
    
    async def run_full_optimization_cycle(self) -> Dict[str, Any]:
        """
        Запускает полный цикл оптимизации всех компонентов
        
        Returns:
            Результаты полного цикла оптимизации
        """
        try:
            cycle_start = datetime.now()
            results = {
                "cycle_start": cycle_start.isoformat(),
                "promotion_results": {},
                "demotion_results": {},
                "eviction_results": {},
                "performance_metrics": {}
            }
            
            logger.info("Starting full optimization cycle")
            
            # 1. Продвижение данных
            if self.data_promoter:
                promotion_start = datetime.now()
                promotion_results = await self.data_promoter.run_promotion_cycle()
                promotion_time = (datetime.now() - promotion_start).total_seconds()
                
                results["promotion_results"] = promotion_results
                results["performance_metrics"]["promotion_time_sec"] = promotion_time
                
                if isinstance(promotion_results, dict):
                    self.enhanced_stats["promotions_executed"] += promotion_results.get("total_promoted", 0)
                
                logger.info(f"Promotion cycle completed in {promotion_time:.2f}s")
            
            # 2. Понижение данных
            if self.data_demoter:
                demotion_start = datetime.now()
                demotion_results = await self.data_demoter.run_demotion_cycle()
                demotion_time = (datetime.now() - demotion_start).total_seconds()
                
                results["demotion_results"] = demotion_results
                results["performance_metrics"]["demotion_time_sec"] = demotion_time
                
                if isinstance(demotion_results, dict):
                    self.enhanced_stats["demotions_executed"] += demotion_results.get("total_demoted", 0)
                
                logger.info(f"Demotion cycle completed in {demotion_time:.2f}s")
            
            # 3. Удаление устаревших данных
            if self.data_evictor:
                eviction_start = datetime.now()
                eviction_results = await self.data_evictor.run_eviction_cycle()
                eviction_time = (datetime.now() - eviction_start).total_seconds()
                
                results["eviction_results"] = eviction_results
                results["performance_metrics"]["eviction_time_sec"] = eviction_time
                
                if isinstance(eviction_results, dict):
                    self.enhanced_stats["evictions_executed"] += eviction_results.get("total_evicted", 0)
                
                logger.info(f"Eviction cycle completed in {eviction_time:.2f}s")
            
            # Общие метрики производительности
            cycle_end = datetime.now()
            total_time = (cycle_end - cycle_start).total_seconds()
            
            results["cycle_end"] = cycle_end.isoformat()
            results["performance_metrics"]["total_cycle_time_sec"] = total_time
            
            # Сохраняем в статистику
            self.enhanced_stats["last_full_cycle"] = cycle_end
            self.enhanced_stats["cycle_performance"].append({
                "timestamp": cycle_end.isoformat(),
                "duration_sec": total_time,
                "promotions": results["promotion_results"].get("total_promoted", 0) if results["promotion_results"] else 0,
                "demotions": results["demotion_results"].get("total_demoted", 0) if results["demotion_results"] else 0,
                "evictions": results["eviction_results"].get("total_evicted", 0) if results["eviction_results"] else 0
            })
            
            # Ограничиваем историю производительности
            if len(self.enhanced_stats["cycle_performance"]) > 100:
                self.enhanced_stats["cycle_performance"] = self.enhanced_stats["cycle_performance"][-100:]
            
            logger.info(f"Full optimization cycle completed in {total_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in full optimization cycle: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Получает комплексную статистику системы"""
        try:
            stats = {
                "base_controller_stats": await self.get_stats(),
                "enhanced_stats": self.enhanced_stats.copy(),
                "storage_stats": {},
                "component_stats": {}
            }
            
            # Статистика хранилища
            if self.multi_storage:
                stats["storage_stats"] = await self.multi_storage.get_storage_stats()
            
            # Статистика компонентов
            if self.data_promoter:
                stats["component_stats"]["promoter"] = self.data_promoter.get_promotion_stats()
            
            if self.data_demoter:
                stats["component_stats"]["demoter"] = self.data_demoter.get_demotion_stats()
            
            if self.data_evictor:
                stats["component_stats"]["evictor"] = self.data_evictor.get_eviction_stats()
            
            # Производные метрики
            stats["derived_metrics"] = self._calculate_derived_metrics(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {"error": str(e)}
    
    def _calculate_derived_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитывает производные метрики"""
        try:
            metrics = {}
            
            # Эффективность оптимизации
            enhanced = stats.get("enhanced_stats", {})
            total_processed = enhanced.get("total_fragments_processed", 0)
            
            if total_processed > 0:
                metrics["promotion_rate"] = enhanced.get("promotions_executed", 0) / total_processed
                metrics["demotion_rate"] = enhanced.get("demotions_executed", 0) / total_processed
                metrics["eviction_rate"] = enhanced.get("evictions_executed", 0) / total_processed
            
            # Производительность циклов
            cycle_perf = enhanced.get("cycle_performance", [])
            if cycle_perf:
                recent_cycles = cycle_perf[-10:]  # Последние 10 циклов
                avg_duration = sum(c.get("duration_sec", 0) for c in recent_cycles) / len(recent_cycles)
                metrics["avg_cycle_duration_sec"] = avg_duration
                
                # Тренд производительности
                if len(recent_cycles) >= 5:
                    first_half = recent_cycles[:len(recent_cycles)//2]
                    second_half = recent_cycles[len(recent_cycles)//2:]
                    
                    first_avg = sum(c.get("duration_sec", 0) for c in first_half) / len(first_half)
                    second_avg = sum(c.get("duration_sec", 0) for c in second_half) / len(second_half)
                    
                    metrics["performance_trend"] = "improving" if second_avg < first_avg else "degrading"
            
            # Утилизация хранилища
            storage_stats = stats.get("storage_stats", {})
            level_stats = storage_stats.get("level_stats", {})
            
            total_fragments = 0
            total_utilization = 0
            active_levels = 0
            
            for level_name, level_data in level_stats.items():
                if isinstance(level_data, dict) and "fragment_count" in level_data:
                    total_fragments += level_data.get("fragment_count", 0)
                    total_utilization += level_data.get("utilization", 0)
                    active_levels += 1
            
            if active_levels > 0:
                metrics["avg_level_utilization"] = total_utilization / active_levels
                metrics["total_fragments_stored"] = total_fragments
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating derived metrics: {e}")
            return {}
    
    async def emergency_optimization(self, target_utilization: float = 0.7) -> Dict[str, Any]:
        """
        Экстренная оптимизация при критической загрузке
        
        Args:
            target_utilization: Целевая загрузка системы (0.0-1.0)
            
        Returns:
            Результаты экстренной оптимизации
        """
        try:
            logger.warning(f"Starting emergency optimization (target: {target_utilization})")
            
            results = {
                "emergency_optimization": True,
                "target_utilization": target_utilization,
                "actions_taken": []
            }
            
            # 1. Экстренная очистка на каждом уровне
            if self.data_evictor:
                for level in MemoryLevel:
                    try:
                        cleanup_result = await self.data_evictor.emergency_cleanup(level, target_utilization)
                        results["actions_taken"].append({
                            "action": "emergency_cleanup",
                            "level": level.value,
                            "result": cleanup_result
                        })
                    except Exception as e:
                        logger.error(f"Emergency cleanup failed for {level}: {e}")
            
            # 2. Принудительное понижение с переполненных уровней
            if self.data_demoter:
                for level in [MemoryLevel.L1, MemoryLevel.L2, MemoryLevel.L3]:
                    try:
                        candidates = await self.data_demoter.analyze_demotion_candidates(level, force_eviction=True)
                        if candidates:
                            next_level = MemoryLevel(level.value + 1) if level.value < 4 else MemoryLevel.L4
                            demotion_result = await self.data_demoter.demote_fragments(candidates[:20], next_level)
                            results["actions_taken"].append({
                                "action": "force_demotion",
                                "from_level": level.value,
                                "to_level": next_level.value,
                                "result": demotion_result
                            })
                    except Exception as e:
                        logger.error(f"Force demotion failed for {level}: {e}")
            
            # 3. Очистка дубликатов
            if self.data_evictor:
                for level in MemoryLevel:
                    try:
                        duplicate_result = await self.data_evictor.cleanup_duplicates(level)
                        if duplicate_result.get("removed", 0) > 0:
                            results["actions_taken"].append({
                                "action": "cleanup_duplicates",
                                "level": level.value,
                                "result": duplicate_result
                            })
                    except Exception as e:
                        logger.error(f"Duplicate cleanup failed for {level}: {e}")
            
            logger.warning(f"Emergency optimization completed: {len(results['actions_taken'])} actions taken")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in emergency optimization: {e}")
            return {"status": "error", "error": str(e)}
    
    async def migrate_fragments_between_levels(self, from_level: MemoryLevel, 
                                              to_level: MemoryLevel, max_count: int = 10) -> Dict[str, Any]:
        """Перемещает фрагменты между уровнями"""
        try:
            if not self.multi_storage:
                return {"status": "storage_not_available"}
            
            # Получаем кандидатов для миграции
            candidates = await self.multi_storage.get_fragments_by_level(from_level, max_count)
            
            if not candidates:
                return {"status": "no_candidates", "migrated": 0}
            
            # Формируем список миграций
            migrations = [(frag.id, from_level, to_level) for frag in candidates]
            
            # Выполняем пакетную миграцию
            result = await self.multi_storage.batch_migrate(migrations)
            
            logger.info(f"Migrated {result.get('successful', 0)} fragments from {from_level} to {to_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error migrating fragments: {e}")
            return {"status": "error", "error": str(e)}
    
    async def rebalance_storage_levels(self) -> Dict[str, Any]:
        """Перебалансирует данные между уровнями хранения"""
        try:
            logger.info("Starting storage rebalancing")
            
            rebalance_results = {
                "migrations_performed": [],
                "total_fragments_moved": 0
            }
            
            # Получаем статистику всех уровней
            if not self.multi_storage:
                return {"status": "storage_not_available"}
            
            storage_stats = await self.multi_storage.get_storage_stats()
            level_stats = storage_stats.get("level_stats", {})
            
            # Анализируем загрузку уровней и планируем миграции
            for level_name, stats in level_stats.items():
                if not isinstance(stats, dict):
                    continue
                
                utilization = stats.get("utilization", 0)
                level = MemoryLevel(level_name)
                
                # Если уровень переполнен (> 80%), мигрируем на следующий
                if utilization > 0.8 and level.value < 4:
                    target_level = MemoryLevel(level.value + 1)
                    migration_count = min(20, int(stats.get("fragment_count", 0) * 0.2))  # 20% фрагментов
                    
                    if migration_count > 0:
                        migration_result = await self.migrate_fragments_between_levels(
                            level, target_level, migration_count
                        )
                        
                        rebalance_results["migrations_performed"].append({
                            "from_level": level.value,
                            "to_level": target_level.value,
                            "result": migration_result
                        })
                        
                        rebalance_results["total_fragments_moved"] += migration_result.get("successful", 0)
            
            logger.info(f"Storage rebalancing completed: {rebalance_results['total_fragments_moved']} fragments moved")
            
            return rebalance_results
            
        except Exception as e:
            logger.error(f"Error rebalancing storage: {e}")
            return {"status": "error", "error": str(e)}
