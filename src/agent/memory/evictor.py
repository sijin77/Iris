"""
DataEvictor - компонент для удаления устаревших данных из системы памяти.
Управляет жизненным циклом данных и освобождает место для новых фрагментов.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta

from .interfaces import IDataEvictor, IMemoryStorage
from .models import MemoryFragment, MemoryLevel, MemoryConfig

logger = logging.getLogger(__name__)


class DataEvictor(IDataEvictor):
    """
    Компонент для автоматического удаления устаревших данных.
    
    Критерии для удаления:
    - Истечение TTL (Time To Live)
    - Переполнение хранилища
    - Низкая ценность данных
    - Дублирование контента
    - Устаревшие эмоциональные связи
    """
    
    def __init__(self, storage: IMemoryStorage, config: MemoryConfig):
        self.storage = storage
        self.config = config
        
        # Статистика работы
        self.stats = {
            "total_evictions": 0,
            "successful_evictions": 0,
            "failed_evictions": 0,
            "last_eviction_time": None,
            "evictions_by_level": {level: 0 for level in MemoryLevel},
            "eviction_reasons": {},
            "bytes_freed": 0,
            "fragments_analyzed": 0
        }
        
        # Настройки TTL для разных уровней (в часах)
        self.default_ttl = {
            MemoryLevel.L1: 24,      # 1 день
            MemoryLevel.L2: 168,     # 7 дней
            MemoryLevel.L3: 720,     # 30 дней
            MemoryLevel.L4: 8760     # 1 год
        }
        
        # Настройки вытеснения
        self.eviction_policies = {
            MemoryLevel.L1: "lru_priority",  # Least Recently Used + низкий приоритет
            MemoryLevel.L2: "lfu_age",       # Least Frequently Used + возраст
            MemoryLevel.L3: "ttl_priority",  # TTL + приоритет
            MemoryLevel.L4: "ttl_only"       # Только TTL
        }
        
        # Пороги для принудительного вытеснения
        self.capacity_thresholds = {
            MemoryLevel.L1: 0.9,   # 90%
            MemoryLevel.L2: 0.85,  # 85%
            MemoryLevel.L3: 0.8,   # 80%
            MemoryLevel.L4: 0.95   # 95%
        }
        
        # Защищенные фрагменты (не подлежат удалению)
        self.protected_fragments: Set[str] = set()
        
        logger.info("DataEvictor initialized")
    
    async def analyze_eviction_candidates(self, level: MemoryLevel, 
                                        force_eviction: bool = False) -> List[MemoryFragment]:
        """
        Анализирует кандидатов для удаления на указанном уровне
        
        Args:
            level: Уровень памяти для анализа
            force_eviction: Принудительное вытеснение при переполнении
            
        Returns:
            Список фрагментов-кандидатов для удаления
        """
        try:
            # Получаем статистику уровня
            level_stats = await self.storage.get_level_statistics(level)
            if not level_stats:
                return []
            
            current_utilization = level_stats.get("utilization", 0.0)
            threshold = self.capacity_thresholds.get(level, 0.9)
            
            # Если уровень не переполнен и не принудительное вытеснение, ищем только просроченные
            if current_utilization < threshold and not force_eviction:
                return await self._find_expired_fragments(level)
            
            # Получаем все фрагменты с уровня
            all_fragments = await self.storage.get_fragments_by_level(level)
            if not all_fragments:
                return []
            
            candidates = []
            current_time = datetime.now()
            policy = self.eviction_policies.get(level, "lru_priority")
            
            for fragment in all_fragments:
                # Пропускаем защищенные фрагменты
                if fragment.id in self.protected_fragments:
                    continue
                
                # Анализируем фрагмент
                should_evict, reason = self._should_evict_fragment(
                    fragment, level, current_time, policy, force_eviction
                )
                
                if should_evict:
                    # Добавляем метаданные о причине удаления
                    if not hasattr(fragment, 'metadata'):
                        fragment.metadata = {}
                    fragment.metadata.update({
                        "eviction_reason": reason,
                        "eviction_analysis_time": current_time.isoformat(),
                        "level_utilization": current_utilization
                    })
                    candidates.append(fragment)
            
            # Сортируем кандидатов по политике вытеснения
            candidates = self._sort_eviction_candidates(candidates, policy)
            
            # Ограничиваем количество для безопасности
            max_evictions = min(len(candidates), int(len(all_fragments) * 0.3))  # Максимум 30%
            candidates = candidates[:max_evictions]
            
            self.stats["fragments_analyzed"] += len(all_fragments)
            
            logger.debug(f"Found {len(candidates)} eviction candidates for level {level} (policy: {policy})")
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error analyzing eviction candidates: {e}")
            return []
    
    async def _find_expired_fragments(self, level: MemoryLevel) -> List[MemoryFragment]:
        """Находит просроченные фрагменты по TTL"""
        try:
            all_fragments = await self.storage.get_fragments_by_level(level)
            expired = []
            current_time = datetime.now()
            ttl_hours = self.default_ttl.get(level, 24)
            
            for fragment in all_fragments:
                if fragment.id in self.protected_fragments:
                    continue
                
                # Проверяем TTL
                age_hours = (current_time.timestamp() - fragment.timestamp) / 3600
                if age_hours > ttl_hours:
                    if not hasattr(fragment, 'metadata'):
                        fragment.metadata = {}
                    fragment.metadata["eviction_reason"] = f"ttl_expired_{age_hours:.1f}h"
                    expired.append(fragment)
            
            return expired
            
        except Exception as e:
            logger.error(f"Error finding expired fragments: {e}")
            return []
    
    def _should_evict_fragment(self, fragment: MemoryFragment, level: MemoryLevel,
                              current_time: datetime, policy: str, force_eviction: bool) -> Tuple[bool, str]:
        """Определяет, нужно ли удалить фрагмент"""
        
        # Всегда проверяем TTL
        ttl_hours = self.default_ttl.get(level, 24)
        age_hours = (current_time.timestamp() - fragment.timestamp) / 3600
        
        if age_hours > ttl_hours:
            return True, f"ttl_expired_{age_hours:.1f}h"
        
        # Если не принудительное вытеснение, проверяем только TTL
        if not force_eviction:
            return False, "not_expired"
        
        # Применяем политику вытеснения
        if policy == "lru_priority":
            # LRU + низкий приоритет
            last_access_hours = (current_time.timestamp() - fragment.last_access_time) / 3600
            if last_access_hours > 12 and fragment.priority < 0.3:
                return True, f"lru_low_priority_{last_access_hours:.1f}h_p{fragment.priority:.2f}"
        
        elif policy == "lfu_age":
            # LFU + возраст
            if fragment.access_count < 2 and age_hours > 48:
                return True, f"lfu_old_{fragment.access_count}acc_{age_hours:.1f}h"
        
        elif policy == "ttl_priority":
            # TTL + приоритет
            if age_hours > ttl_hours * 0.7 and fragment.priority < 0.4:
                return True, f"aging_low_priority_{age_hours:.1f}h_p{fragment.priority:.2f}"
        
        # Проверяем специфические критерии
        
        # Дублированный контент
        if hasattr(fragment, 'metadata') and fragment.metadata:
            if fragment.metadata.get("duplicate_detected", False):
                return True, "duplicate_content"
        
        # Устаревшие эмоциональные связи
        if fragment.metadata and fragment.metadata.get("emotional_weight", 0) > 0:
            emotional_age_hours = age_hours
            decay_threshold = 72  # 3 дня
            if emotional_age_hours > decay_threshold and fragment.priority < 0.2:
                return True, f"emotional_decay_{emotional_age_hours:.1f}h"
        
        # Низкое качество данных
        if fragment.priority < 0.1 and fragment.access_count == 0:
            return True, f"low_quality_unused"
        
        return False, "keep_fragment"
    
    def _sort_eviction_candidates(self, candidates: List[MemoryFragment], policy: str) -> List[MemoryFragment]:
        """Сортирует кандидатов по политике вытеснения"""
        
        if policy == "lru_priority":
            # Сначала давно не использованные с низким приоритетом
            candidates.sort(key=lambda f: (f.last_access_time, f.priority))
        
        elif policy == "lfu_age":
            # Сначала редко используемые и старые
            candidates.sort(key=lambda f: (f.access_count, -f.timestamp))
        
        elif policy == "ttl_priority":
            # Сначала старые с низким приоритетом
            candidates.sort(key=lambda f: (-f.timestamp, f.priority))
        
        elif policy == "ttl_only":
            # Только по возрасту
            candidates.sort(key=lambda f: f.timestamp)
        
        else:
            # По умолчанию: приоритет + возраст
            candidates.sort(key=lambda f: (f.priority, f.timestamp))
        
        return candidates
    
    async def evict_fragments(self, candidates: List[MemoryFragment]) -> Dict[str, any]:
        """
        Удаляет фрагменты из памяти
        
        Args:
            candidates: Список фрагментов для удаления
            
        Returns:
            Результат операции удаления
        """
        if not candidates:
            return {"status": "no_candidates", "evicted": 0, "failed": 0}
        
        try:
            evicted_count = 0
            failed_count = 0
            bytes_freed = 0
            eviction_details = []
            
            for fragment in candidates:
                try:
                    # Рассчитываем размер фрагмента (приблизительно)
                    fragment_size = len(fragment.content.encode('utf-8')) if fragment.content else 0
                    fragment_size += len(str(fragment.metadata).encode('utf-8')) if hasattr(fragment, 'metadata') and fragment.metadata else 0
                    
                    # Удаляем фрагмент
                    success = await self.storage.delete_fragment(fragment.id, fragment.level)
                    
                    if success:
                        evicted_count += 1
                        bytes_freed += fragment_size
                        self.stats["successful_evictions"] += 1
                        self.stats["evictions_by_level"][fragment.level] += 1
                        
                        # Записываем причину удаления
                        reason = fragment.metadata.get("eviction_reason", "unknown") if hasattr(fragment, 'metadata') and fragment.metadata else "unknown"
                        self.stats["eviction_reasons"][reason] = \
                            self.stats["eviction_reasons"].get(reason, 0) + 1
                        
                        eviction_details.append({
                            "fragment_id": fragment.id,
                            "level": fragment.level.value,
                            "reason": reason,
                            "size_bytes": fragment_size,
                            "priority": fragment.priority,
                            "age_hours": (datetime.now().timestamp() - fragment.timestamp) / 3600
                        })
                        
                        logger.debug(f"Evicted fragment {fragment.id} from {fragment.level} (reason: {reason})")
                    else:
                        failed_count += 1
                        self.stats["failed_evictions"] += 1
                        
                except Exception as e:
                    logger.error(f"Error evicting fragment {fragment.id}: {e}")
                    failed_count += 1
                    self.stats["failed_evictions"] += 1
            
            # Обновляем общую статистику
            self.stats["total_evictions"] += evicted_count + failed_count
            self.stats["bytes_freed"] += bytes_freed
            self.stats["last_eviction_time"] = datetime.now()
            
            result = {
                "status": "completed",
                "evicted": evicted_count,
                "failed": failed_count,
                "bytes_freed": bytes_freed,
                "details": eviction_details
            }
            
            logger.info(f"Eviction completed: {evicted_count} fragments evicted, {bytes_freed} bytes freed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in evict_fragments: {e}")
            return {"status": "error", "error": str(e), "evicted": 0, "failed": len(candidates)}
    
    async def run_eviction_cycle(self, force_eviction: bool = False) -> Dict[str, any]:
        """
        Выполняет полный цикл очистки для всех уровней
        
        Args:
            force_eviction: Принудительная очистка при переполнении
            
        Returns:
            Результат цикла очистки
        """
        try:
            cycle_results = {}
            total_evicted = 0
            total_bytes_freed = 0
            
            # Очищаем каждый уровень
            for level in MemoryLevel:
                try:
                    candidates = await self.analyze_eviction_candidates(level, force_eviction)
                    
                    if candidates:
                        result = await self.evict_fragments(candidates)
                        cycle_results[f"{level.value}_eviction"] = result
                        total_evicted += result.get("evicted", 0)
                        total_bytes_freed += result.get("bytes_freed", 0)
                    else:
                        cycle_results[f"{level.value}_eviction"] = {
                            "status": "no_candidates",
                            "evicted": 0,
                            "bytes_freed": 0
                        }
                        
                except Exception as e:
                    logger.error(f"Error processing level {level}: {e}")
                    cycle_results[f"{level.value}_eviction"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            cycle_results["summary"] = {
                "total_evicted": total_evicted,
                "total_bytes_freed": total_bytes_freed,
                "cycle_time": datetime.now().isoformat(),
                "force_eviction": force_eviction
            }
            
            logger.info(f"Eviction cycle completed: {total_evicted} fragments evicted, {total_bytes_freed} bytes freed")
            
            return cycle_results
            
        except Exception as e:
            logger.error(f"Error in eviction cycle: {e}")
            return {"status": "error", "error": str(e)}
    
    def protect_fragments(self, fragment_ids: List[str]):
        """Защищает фрагменты от удаления"""
        self.protected_fragments.update(fragment_ids)
        logger.info(f"Protected {len(fragment_ids)} fragments from eviction")
    
    def unprotect_fragments(self, fragment_ids: List[str]):
        """Снимает защиту с фрагментов"""
        self.protected_fragments.difference_update(fragment_ids)
        logger.info(f"Unprotected {len(fragment_ids)} fragments")
    
    def configure_ttl(self, level: MemoryLevel, ttl_hours: int):
        """Настраивает TTL для уровня"""
        self.default_ttl[level] = ttl_hours
        logger.info(f"Updated TTL for {level} to {ttl_hours} hours")
    
    def configure_policy(self, level: MemoryLevel, policy: str):
        """Настраивает политику вытеснения для уровня"""
        valid_policies = ["lru_priority", "lfu_age", "ttl_priority", "ttl_only"]
        if policy in valid_policies:
            self.eviction_policies[level] = policy
            logger.info(f"Updated eviction policy for {level} to {policy}")
        else:
            logger.warning(f"Invalid eviction policy: {policy}. Valid options: {valid_policies}")
    
    def get_eviction_stats(self) -> Dict[str, any]:
        """Получает статистику работы эвиктора"""
        stats = self.stats.copy()
        
        # Добавляем производные метрики
        if stats["total_evictions"] > 0:
            stats["success_rate"] = stats["successful_evictions"] / stats["total_evictions"]
        else:
            stats["success_rate"] = 0.0
        
        stats["protected_fragments_count"] = len(self.protected_fragments)
        stats["current_ttl_config"] = self.default_ttl.copy()
        stats["current_policies"] = self.eviction_policies.copy()
        stats["capacity_thresholds"] = self.capacity_thresholds.copy()
        
        return stats
    
    async def emergency_cleanup(self, level: MemoryLevel, target_utilization: float = 0.7) -> Dict[str, any]:
        """
        Экстренная очистка уровня до указанного процента загрузки
        
        Args:
            level: Уровень для очистки
            target_utilization: Целевая загрузка (0.0-1.0)
            
        Returns:
            Результат экстренной очистки
        """
        try:
            # Получаем текущую статистику
            level_stats = await self.storage.get_level_statistics(level)
            if not level_stats:
                return {"status": "no_stats", "evicted": 0}
            
            current_utilization = level_stats.get("utilization", 0.0)
            
            if current_utilization <= target_utilization:
                return {"status": "not_needed", "current_utilization": current_utilization}
            
            # Рассчитываем, сколько нужно освободить
            total_fragments = level_stats.get("fragment_count", 0)
            target_fragments = int(total_fragments * target_utilization)
            fragments_to_remove = total_fragments - target_fragments
            
            # Получаем кандидатов для удаления
            candidates = await self.analyze_eviction_candidates(level, force_eviction=True)
            
            # Ограничиваем количество удаляемых фрагментов
            candidates = candidates[:fragments_to_remove]
            
            # Выполняем удаление
            result = await self.evict_fragments(candidates)
            result["emergency_cleanup"] = True
            result["target_utilization"] = target_utilization
            result["initial_utilization"] = current_utilization
            
            logger.warning(f"Emergency cleanup on {level}: removed {result.get('evicted', 0)} fragments")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in emergency cleanup: {e}")
            return {"status": "error", "error": str(e)}
    
    async def find_duplicate_fragments(self, level: MemoryLevel) -> List[Tuple[str, str]]:
        """
        Находит дублированные фрагменты на уровне
        
        Args:
            level: Уровень для поиска дубликатов
            
        Returns:
            Список пар (original_id, duplicate_id)
        """
        try:
            fragments = await self.storage.get_fragments_by_level(level)
            if not fragments:
                return []
            
            # Группируем по хешу контента
            content_hashes = {}
            duplicates = []
            
            for fragment in fragments:
                if not fragment.content:
                    continue
                
                # Простой хеш контента
                content_hash = hash(fragment.content.strip().lower())
                
                if content_hash in content_hashes:
                    # Найден дубликат
                    original_id = content_hashes[content_hash]
                    duplicates.append((original_id, fragment.id))
                    
                    # Помечаем как дубликат
                    if not hasattr(fragment, 'metadata'):
                        fragment.metadata = {}
                    fragment.metadata["duplicate_detected"] = True
                    fragment.metadata["original_fragment"] = original_id
                    
                else:
                    content_hashes[content_hash] = fragment.id
            
            logger.info(f"Found {len(duplicates)} duplicate fragments on {level}")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    async def cleanup_duplicates(self, level: MemoryLevel) -> Dict[str, any]:
        """Удаляет дублированные фрагменты"""
        try:
            duplicates = await self.find_duplicate_fragments(level)
            
            if not duplicates:
                return {"status": "no_duplicates", "removed": 0}
            
            # Получаем дублированные фрагменты для удаления
            duplicate_ids = [dup_id for _, dup_id in duplicates]
            duplicate_fragments = []
            
            for fragment_id in duplicate_ids:
                fragment = await self.storage.get_fragment(fragment_id)
                if fragment:
                    duplicate_fragments.append(fragment)
            
            # Удаляем дубликаты
            result = await self.evict_fragments(duplicate_fragments)
            result["type"] = "duplicate_cleanup"
            result["duplicates_found"] = len(duplicates)
            
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning up duplicates: {e}")
            return {"status": "error", "error": str(e)}
