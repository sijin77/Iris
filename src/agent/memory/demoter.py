"""
DataDemoter - компонент для понижения приоритета данных в системе памяти.
Автоматически перемещает данные на более "холодные" уровни хранения.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .interfaces import IDataDemoter, IMemoryStorage
from .models import MemoryFragment, MemoryLevel, AccessPattern, MemoryConfig

logger = logging.getLogger(__name__)


class DataDemoter(IDataDemoter):
    """
    Компонент для автоматического понижения приоритета и перемещения данных
    на более холодные уровни хранения.
    
    Критерии для понижения:
    - Низкая частота доступа
    - Давность последнего доступа
    - Низкий приоритет фрагмента
    - Переполнение текущего уровня
    """
    
    def __init__(self, storage: IMemoryStorage, config: MemoryConfig):
        self.storage = storage
        self.config = config
        
        # Статистика работы
        self.stats = {
            "total_demotions": 0,
            "successful_demotions": 0,
            "failed_demotions": 0,
            "last_demotion_time": None,
            "demotions_by_level": {level: 0 for level in MemoryLevel},
            "demotion_reasons": {}
        }
        
        # Кэш решений для оптимизации
        self.demotion_cache: Dict[str, Tuple[bool, str, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)
        
        # Настройки демоции
        self.demotion_thresholds = {
            MemoryLevel.L1: {
                "max_age_hours": 24,
                "min_access_frequency": 2,
                "priority_threshold": 0.3,
                "capacity_threshold": 0.8
            },
            MemoryLevel.L2: {
                "max_age_hours": 168,  # 7 дней
                "min_access_frequency": 1,
                "priority_threshold": 0.2,
                "capacity_threshold": 0.9
            },
            MemoryLevel.L3: {
                "max_age_hours": 720,  # 30 дней
                "min_access_frequency": 0,
                "priority_threshold": 0.1,
                "capacity_threshold": 0.95
            }
        }
        
        logger.info("DataDemoter initialized")
    
    async def analyze_demotion_candidates(self, level: MemoryLevel, limit: int = 100) -> List[MemoryFragment]:
        """
        Анализирует кандидатов для понижения на указанном уровне
        
        Args:
            level: Уровень памяти для анализа
            limit: Максимальное количество кандидатов
            
        Returns:
            Список фрагментов-кандидатов для понижения
        """
        try:
            # Получаем все фрагменты с указанного уровня
            fragments = await self.storage.get_fragments_by_level(level, limit * 2)
            
            if not fragments:
                return []
            
            candidates = []
            thresholds = self.demotion_thresholds.get(level, {})
            current_time = datetime.now()
            
            for fragment in fragments:
                # Проверяем кэш решений
                cache_key = f"{fragment.id}_{level.value}"
                if cache_key in self.demotion_cache:
                    should_demote, reason, cache_time = self.demotion_cache[cache_key]
                    if current_time - cache_time < self.cache_ttl:
                        if should_demote:
                            candidates.append(fragment)
                        continue
                
                # Анализируем кандидата
                should_demote, reason = self._should_demote_fragment(fragment, level, thresholds, current_time)
                
                # Кэшируем решение
                self.demotion_cache[cache_key] = (should_demote, reason, current_time)
                
                if should_demote:
                    candidates.append(fragment)
                    
                    # Добавляем причину в метаданные
                    if not hasattr(fragment, 'metadata'):
                        fragment.metadata = {}
                    fragment.metadata["demotion_reason"] = reason
                    fragment.metadata["demotion_analysis_time"] = current_time.isoformat()
            
            # Сортируем кандидатов по приоритету (сначала с наименьшим приоритетом)
            candidates.sort(key=lambda f: (f.priority, f.last_access_time))
            
            logger.debug(f"Found {len(candidates)} demotion candidates for level {level}")
            
            return candidates[:limit]
            
        except Exception as e:
            logger.error(f"Error analyzing demotion candidates: {e}")
            return []
    
    def _should_demote_fragment(self, fragment: MemoryFragment, level: MemoryLevel, 
                               thresholds: Dict, current_time: datetime) -> Tuple[bool, str]:
        """Определяет, нужно ли понизить фрагмент"""
        
        # Вычисляем возраст фрагмента
        age_hours = (current_time.timestamp() - fragment.last_access_time) / 3600
        
        # Критерий 1: Слишком старый
        max_age = thresholds.get("max_age_hours", 24)
        if age_hours > max_age:
            return True, f"age_exceeded_{age_hours:.1f}h"
        
        # Критерий 2: Низкая частота доступа
        min_frequency = thresholds.get("min_access_frequency", 1)
        if fragment.access_count < min_frequency:
            return True, f"low_frequency_{fragment.access_count}"
        
        # Критерий 3: Низкий приоритет
        priority_threshold = thresholds.get("priority_threshold", 0.3)
        if fragment.priority < priority_threshold:
            return True, f"low_priority_{fragment.priority:.2f}"
        
        # Критерий 4: Проверяем загруженность уровня
        capacity_threshold = thresholds.get("capacity_threshold", 0.8)
        try:
            level_stats = asyncio.run(self.storage.get_level_statistics(level))
            if level_stats and level_stats.get("utilization", 0) > capacity_threshold:
                # Если уровень переполнен, понижаем фрагменты с низким приоритетом
                if fragment.priority < 0.5:
                    return True, f"capacity_pressure_{level_stats['utilization']:.2f}"
        except:
            pass  # Игнорируем ошибки получения статистики
        
        # Критерий 5: Эмоциональное затухание (для эмоциональных фрагментов)
        if hasattr(fragment, 'metadata') and fragment.metadata:
            emotional_weight = fragment.metadata.get("emotional_weight", 0)
            if emotional_weight > 0:
                # Эмоциональные фрагменты затухают со временем
                decay_rate = 0.1  # 10% в час
                current_emotional_weight = emotional_weight * (1 - decay_rate * age_hours / 24)
                if current_emotional_weight < 0.1:
                    return True, f"emotional_decay_{current_emotional_weight:.2f}"
        
        return False, "no_demotion_needed"
    
    async def demote_fragments(self, candidates: List[MemoryFragment], 
                              target_level: MemoryLevel) -> Dict[str, any]:
        """
        Понижает фрагменты на указанный уровень
        
        Args:
            candidates: Список фрагментов для понижения
            target_level: Целевой уровень
            
        Returns:
            Результат операции понижения
        """
        if not candidates:
            return {"status": "no_candidates", "demoted": 0, "failed": 0}
        
        try:
            demoted_count = 0
            failed_count = 0
            demotion_details = []
            
            for fragment in candidates:
                try:
                    # Определяем текущий уровень фрагмента
                    current_level = fragment.level
                    
                    # Проверяем, что целевой уровень действительно "холоднее"
                    if not self._is_valid_demotion(current_level, target_level):
                        failed_count += 1
                        continue
                    
                    # Обновляем метаданные фрагмента
                    if not hasattr(fragment, 'metadata'):
                        fragment.metadata = {}
                    
                    fragment.metadata.update({
                        "demoted_from": current_level.value,
                        "demoted_to": target_level.value,
                        "demotion_time": datetime.now().isoformat(),
                        "demotion_reason": fragment.metadata.get("demotion_reason", "unknown")
                    })
                    
                    # Понижаем приоритет при демоции
                    old_priority = fragment.priority
                    fragment.priority *= 0.8  # Снижаем на 20%
                    fragment.level = target_level
                    
                    # Сохраняем фрагмент на новом уровне
                    success = await self.storage.store_fragment(fragment, target_level)
                    
                    if success:
                        # Удаляем с старого уровня
                        await self.storage.delete_fragment(fragment.id, current_level)
                        
                        demoted_count += 1
                        self.stats["successful_demotions"] += 1
                        self.stats["demotions_by_level"][target_level] += 1
                        
                        # Записываем причину демоции
                        reason = fragment.metadata.get("demotion_reason", "unknown")
                        self.stats["demotion_reasons"][reason] = \
                            self.stats["demotion_reasons"].get(reason, 0) + 1
                        
                        demotion_details.append({
                            "fragment_id": fragment.id,
                            "from_level": current_level.value,
                            "to_level": target_level.value,
                            "old_priority": old_priority,
                            "new_priority": fragment.priority,
                            "reason": reason
                        })
                        
                        logger.debug(f"Demoted fragment {fragment.id} from {current_level} to {target_level}")
                    else:
                        failed_count += 1
                        self.stats["failed_demotions"] += 1
                        
                except Exception as e:
                    logger.error(f"Error demoting fragment {fragment.id}: {e}")
                    failed_count += 1
                    self.stats["failed_demotions"] += 1
            
            # Обновляем общую статистику
            self.stats["total_demotions"] += demoted_count + failed_count
            self.stats["last_demotion_time"] = datetime.now()
            
            result = {
                "status": "completed",
                "demoted": demoted_count,
                "failed": failed_count,
                "target_level": target_level.value,
                "details": demotion_details
            }
            
            logger.info(f"Demotion completed: {demoted_count} successful, {failed_count} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in demote_fragments: {e}")
            return {"status": "error", "error": str(e), "demoted": 0, "failed": len(candidates)}
    
    def _is_valid_demotion(self, current_level: MemoryLevel, target_level: MemoryLevel) -> bool:
        """Проверяет, является ли демоция валидной (на более холодный уровень)"""
        level_order = {
            MemoryLevel.L1: 1,
            MemoryLevel.L2: 2,
            MemoryLevel.L3: 3,
            MemoryLevel.L4: 4
        }
        
        return level_order.get(target_level, 0) > level_order.get(current_level, 0)
    
    async def run_demotion_cycle(self) -> Dict[str, any]:
        """
        Выполняет полный цикл демоции для всех уровней
        
        Returns:
            Результат цикла демоции
        """
        try:
            cycle_results = {}
            total_demoted = 0
            
            # L1 → L2
            l1_candidates = await self.analyze_demotion_candidates(MemoryLevel.L1, 50)
            if l1_candidates:
                l1_result = await self.demote_fragments(l1_candidates, MemoryLevel.L2)
                cycle_results["L1_to_L2"] = l1_result
                total_demoted += l1_result.get("demoted", 0)
            
            # L2 → L3
            l2_candidates = await self.analyze_demotion_candidates(MemoryLevel.L2, 30)
            if l2_candidates:
                l2_result = await self.demote_fragments(l2_candidates, MemoryLevel.L3)
                cycle_results["L2_to_L3"] = l2_result
                total_demoted += l2_result.get("demoted", 0)
            
            # L3 → L4
            l3_candidates = await self.analyze_demotion_candidates(MemoryLevel.L3, 20)
            if l3_candidates:
                l3_result = await self.demote_fragments(l3_candidates, MemoryLevel.L4)
                cycle_results["L3_to_L4"] = l3_result
                total_demoted += l3_result.get("demoted", 0)
            
            cycle_results["total_demoted"] = total_demoted
            cycle_results["cycle_time"] = datetime.now().isoformat()
            
            logger.info(f"Demotion cycle completed: {total_demoted} fragments demoted")
            
            return cycle_results
            
        except Exception as e:
            logger.error(f"Error in demotion cycle: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_demotion_stats(self) -> Dict[str, any]:
        """Получает статистику работы демотера"""
        stats = self.stats.copy()
        
        # Добавляем производные метрики
        if stats["total_demotions"] > 0:
            stats["success_rate"] = stats["successful_demotions"] / stats["total_demotions"]
        else:
            stats["success_rate"] = 0.0
        
        stats["cache_size"] = len(self.demotion_cache)
        stats["cache_hit_potential"] = len([
            entry for entry in self.demotion_cache.values()
            if datetime.now() - entry[2] < self.cache_ttl
        ])
        
        return stats
    
    def clear_cache(self):
        """Очищает кэш решений о демоции"""
        self.demotion_cache.clear()
        logger.info("Demotion cache cleared")
    
    async def force_demotion(self, fragment_ids: List[str], target_level: MemoryLevel) -> Dict[str, any]:
        """
        Принудительно понижает указанные фрагменты
        
        Args:
            fragment_ids: Список ID фрагментов
            target_level: Целевой уровень
            
        Returns:
            Результат принудительной демоции
        """
        try:
            fragments = []
            
            # Получаем фрагменты по ID
            for fragment_id in fragment_ids:
                fragment = await self.storage.get_fragment(fragment_id)
                if fragment:
                    fragments.append(fragment)
            
            if not fragments:
                return {"status": "no_fragments_found", "demoted": 0}
            
            # Помечаем как принудительную демоцию
            for fragment in fragments:
                if not hasattr(fragment, 'metadata'):
                    fragment.metadata = {}
                fragment.metadata["demotion_reason"] = "force_demotion"
                fragment.metadata["force_demoted"] = True
            
            # Выполняем демоцию
            result = await self.demote_fragments(fragments, target_level)
            result["type"] = "force_demotion"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in force demotion: {e}")
            return {"status": "error", "error": str(e)}
    
    def configure_thresholds(self, level: MemoryLevel, thresholds: Dict[str, any]):
        """Настраивает пороги демоции для уровня"""
        if level in self.demotion_thresholds:
            self.demotion_thresholds[level].update(thresholds)
            logger.info(f"Updated demotion thresholds for {level}: {thresholds}")
        else:
            logger.warning(f"Unknown level for threshold configuration: {level}")
    
    async def cleanup_expired_cache(self):
        """Очищает просроченные записи кэша"""
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, _, cache_time) in self.demotion_cache.items()
            if current_time - cache_time > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.demotion_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
