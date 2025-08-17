"""
DataPromoter - компонент для продвижения важных данных на более высокие уровни памяти.
Анализирует паттерны доступа и автоматически перемещает данные в горячие кэши.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from .models import (
    MemoryFragment, MemoryLevel, AccessPattern, ActivityScore, MemoryConfig
)
from .interfaces import IDataPromoter, IMemoryAnalyzer, IMemoryStorage

logger = logging.getLogger(__name__)


class DataPromoter(IDataPromoter):
    """
    Компонент для продвижения важных данных на более высокие уровни памяти.
    
    Отвечает за:
    - Анализ кандидатов для продвижения
    - Принятие решений о продвижении
    - Выполнение операций продвижения
    - Мониторинг эффективности
    """
    
    def __init__(self, config: MemoryConfig, analyzer: Optional[IMemoryAnalyzer] = None, 
                 storage: Optional[IMemoryStorage] = None):
        self.config = config
        self.analyzer = analyzer
        self.storage = storage
        self.is_initialized = False
        
        # Статистика продвижений
        self.promotions_count = 0
        self.successful_promotions = 0
        self.failed_promotions = 0
        self.last_promotion = None
        
        # Кэш решений для оптимизации
        self._decision_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 минут
        
        logger.info("DataPromoter инициализирован")
    
    async def initialize(self) -> bool:
        """Инициализация компонента"""
        try:
            logger.info("Инициализация DataPromoter...")
            
            # Проверяем зависимости
            if not self.storage:
                logger.warning("DataPromoter: MemoryStorage не установлен")
            
            if not self.analyzer:
                logger.warning("DataPromoter: MemoryAnalyzer не установлен")
            
            self.is_initialized = True
            logger.info("DataPromoter успешно инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации DataPromoter: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Завершение работы компонента"""
        try:
            logger.info("Завершение работы DataPromoter...")
            
            self.is_initialized = False
            self._decision_cache.clear()
            
            logger.info("DataPromoter успешно завершил работу")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка завершения работы DataPromoter: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики компонента"""
        return {
            "promotions_count": self.promotions_count,
            "successful_promotions": self.successful_promotions,
            "failed_promotions": self.failed_promotions,
            "success_rate": (self.successful_promotions / self.promotions_count * 100) if self.promotions_count > 0 else 0,
            "last_promotion": self.last_promotion.isoformat() if self.last_promotion else None,
            "decision_cache_size": len(self._decision_cache),
            "is_initialized": self.is_initialized
        }
    
    async def analyze_promotion_candidates(self, level: MemoryLevel) -> List[MemoryFragment]:
        """
        Анализирует кандидатов для продвижения с указанного уровня.
        
        Args:
            level: Уровень памяти для анализа
            
        Returns:
            Список фрагментов-кандидатов для продвижения
        """
        try:
            if not self.is_initialized:
                logger.warning("DataPromoter не инициализирован")
                return []
            
            logger.debug(f"Анализ кандидатов для продвижения с уровня {level}")
            
            # Получаем все фрагменты с указанного уровня
            fragments = await self._get_fragments_from_level(level)
            if not fragments:
                logger.debug(f"На уровне {level} нет фрагментов для анализа")
                return []
            
            # Анализируем каждый фрагмент
            candidates = []
            for fragment in fragments:
                try:
                    # Получаем паттерн доступа
                    access_pattern = await self._get_access_pattern(fragment)
                    
                    # Проверяем, нужно ли продвигать
                    if await self.should_promote(fragment, access_pattern):
                        candidates.append(fragment)
                        
                except Exception as e:
                    logger.error(f"Ошибка анализа фрагмента {fragment.id}: {e}")
                    continue
            
            logger.info(f"Найдено {len(candidates)} кандидатов для продвижения с уровня {level}")
            return candidates
            
        except Exception as e:
            logger.error(f"Ошибка анализа кандидатов для продвижения: {e}")
            return []
    
    async def should_promote(self, fragment: MemoryFragment, access_pattern: AccessPattern) -> bool:
        """
        Определяет, нужно ли продвигать фрагмент.
        
        Критерии продвижения:
        - Частота доступа ≥ порога продвижения
        - Недавность использования
        - Высокая важность
        """
        try:
            # Проверяем кэш решений
            cache_key = f"{fragment.id}_promotion"
            cached_decision = self._get_cached_decision(cache_key)
            if cached_decision:
                return cached_decision["should_promote"]
            
            # Анализируем критерии
            should_promote = await self._evaluate_promotion_criteria(fragment, access_pattern)
            
            # Кэшируем решение
            self._cache_decision(cache_key, {
                "should_promote": should_promote,
                "timestamp": datetime.utcnow(),
                "reason": await self._get_promotion_reason(fragment, access_pattern, should_promote)
            })
            
            return should_promote
            
        except Exception as e:
            logger.error(f"Ошибка определения необходимости продвижения: {e}")
            return False
    
    async def promote_fragment(self, fragment: MemoryFragment, target_level: MemoryLevel) -> bool:
        """
        Продвигает фрагмент на указанный уровень.
        
        Args:
            fragment: Фрагмент для продвижения
            target_level: Целевой уровень
            
        Returns:
            True если продвижение успешно, False в противном случае
        """
        try:
            if not self.is_initialized:
                logger.warning("DataPromoter не инициализирован")
                return False
            
            logger.info(f"Продвижение фрагмента {fragment.id} с {fragment.current_level} на {target_level}")
            
            # Проверяем валидность перехода
            if not self._is_valid_promotion(fragment.current_level, target_level):
                logger.warning(f"Недопустимый переход: {fragment.current_level} → {target_level}")
                return False
            
            # Проверяем емкость целевого уровня
            if not await self._check_target_level_capacity(target_level):
                logger.warning(f"Недостаточно места на уровне {target_level}")
                return False
            
            # Выполняем продвижение
            success = await self._execute_promotion(fragment, target_level)
            
            # Обновляем статистику
            self._update_promotion_stats(success)
            
            if success:
                logger.info(f"Фрагмент {fragment.id} успешно продвинут на уровень {target_level}")
            else:
                logger.error(f"Не удалось продвинуть фрагмент {fragment.id} на уровень {target_level}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка продвижения фрагмента {fragment.id}: {e}")
            self._update_promotion_stats(False)
            return False
    
    async def batch_promote(self, fragments: List[MemoryFragment]) -> Dict[str, bool]:
        """
        Пакетное продвижение фрагментов.
        
        Args:
            fragments: Список фрагментов для продвижения
            
        Returns:
            Словарь результатов по ID фрагментов
        """
        try:
            if not fragments:
                return {}
            
            logger.info(f"Пакетное продвижение {len(fragments)} фрагментов")
            
            results = {}
            tasks = []
            
            # Создаем задачи для каждого фрагмента
            for fragment in fragments:
                target_level = self._get_target_promotion_level(fragment.current_level)
                task = self.promote_fragment(fragment, target_level)
                tasks.append((fragment.id, task))
            
            # Выполняем все задачи
            for fragment_id, task in tasks:
                try:
                    result = await task
                    results[fragment_id] = result
                except Exception as e:
                    logger.error(f"Ошибка продвижения фрагмента {fragment_id}: {e}")
                    results[fragment_id] = False
            
            # Логируем результаты
            successful = sum(1 for result in results.values() if result)
            logger.info(f"Пакетное продвижение завершено: {successful}/{len(fragments)} успешно")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка пакетного продвижения: {e}")
            return {fragment.id: False for fragment in fragments}
    
    # Приватные методы
    
    async def _get_fragments_from_level(self, level: MemoryLevel) -> List[MemoryFragment]:
        """Получает фрагменты с указанного уровня"""
        try:
            if not self.storage:
                return []
            
            # Получаем информацию о емкости уровня
            capacity_info = await self.storage.get_level_capacity(level)
            if not capacity_info:
                return []
            
            # Получаем фрагменты (здесь нужна реализация в storage)
            # Пока возвращаем пустой список
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения фрагментов с уровня {level}: {e}")
            return []
    
    async def _get_access_pattern(self, fragment: MemoryFragment) -> AccessPattern:
        """Получает паттерн доступа к фрагменту"""
        try:
            if self.analyzer:
                return await self.analyzer.analyze_access_pattern(fragment.id, fragment.user_id)
            else:
                # Fallback: создаем базовый паттерн
                return AccessPattern(
                    fragment_id=fragment.id,
                    user_id=fragment.user_id,
                    frequency=fragment.access_count,
                    importance_score=fragment.priority
                )
                
        except Exception as e:
            logger.error(f"Ошибка получения паттерна доступа: {e}")
            # Возвращаем базовый паттерн
            return AccessPattern(
                fragment_id=fragment.id,
                user_id=fragment.user_id,
                frequency=0,
                importance_score=0.0
            )
    
    async def _evaluate_promotion_criteria(self, fragment: MemoryFragment, access_pattern: AccessPattern) -> bool:
        """Оценивает критерии продвижения"""
        try:
            # Критерий 1: Частота доступа
            frequency_ok = access_pattern.frequency >= self.config.promotion_threshold
            
            # Критерий 2: Недавность использования
            recency_ok = access_pattern.recency_hours <= self.config.recency_threshold
            
            # Критерий 3: Важность
            importance_ok = access_pattern.importance_score >= self.config.importance_threshold
            
            # Дополнительный критерий: приоритет фрагмента
            priority_ok = fragment.priority >= 0.6
            
            # Комбинированное решение
            should_promote = (frequency_ok and recency_ok) or (importance_ok and priority_ok)
            
            logger.debug(f"Критерии продвижения для {fragment.id}: "
                        f"frequency={frequency_ok}, recency={recency_ok}, "
                        f"importance={importance_ok}, priority={priority_ok}, "
                        f"result={should_promote}")
            
            return should_promote
            
        except Exception as e:
            logger.error(f"Ошибка оценки критериев продвижения: {e}")
            return False
    
    def _is_valid_promotion(self, from_level: MemoryLevel, to_level: MemoryLevel) -> bool:
        """Проверяет валидность перехода между уровнями"""
        # L3 → L2 → L1 (только вверх)
        valid_transitions = {
            MemoryLevel.L3_VECTOR: [MemoryLevel.L2_WARM],
            MemoryLevel.L2_WARM: [MemoryLevel.L1_HOT],
            MemoryLevel.L1_HOT: []  # L1 - максимальный уровень
        }
        
        return to_level in valid_transitions.get(from_level, [])
    
    async def _check_target_level_capacity(self, target_level: MemoryLevel) -> bool:
        """Проверяет емкость целевого уровня"""
        try:
            if not self.storage:
                return True  # Если storage не доступен, считаем что место есть
            
            capacity_info = await self.storage.get_level_capacity(target_level)
            usage_info = await self.storage.get_level_usage(target_level)
            
            if not capacity_info or not usage_info:
                return True
            
            # Проверяем, есть ли место
            current_usage = usage_info.get("current_size", 0)
            max_capacity = capacity_info.get("max_size", float('inf'))
            
            return current_usage < max_capacity
            
        except Exception as e:
            logger.error(f"Ошибка проверки емкости уровня {target_level}: {e}")
            return True  # В случае ошибки разрешаем продвижение
    
    async def _execute_promotion(self, fragment: MemoryFragment, target_level: MemoryLevel) -> bool:
        """Выполняет операцию продвижения"""
        try:
            if not self.storage:
                return False
            
            # Перемещаем фрагмент между уровнями
            success = await self.storage.move_fragment(
                fragment, fragment.current_level, target_level
            )
            
            if success:
                # Обновляем уровень фрагмента
                fragment.current_level = target_level
                fragment.last_accessed = datetime.utcnow()
                
                # Обновляем время истечения
                fragment.expires_at = self._calculate_expiration_time(target_level)
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка выполнения продвижения: {e}")
            return False
    
    def _get_target_promotion_level(self, current_level: MemoryLevel) -> MemoryLevel:
        """Определяет целевой уровень для продвижения"""
        promotion_map = {
            MemoryLevel.L3_VECTOR: MemoryLevel.L2_WARM,
            MemoryLevel.L2_WARM: MemoryLevel.L1_HOT
        }
        
        return promotion_map.get(current_level, current_level)
    
    def _calculate_expiration_time(self, level: MemoryLevel) -> datetime:
        """Вычисляет время истечения для уровня"""
        ttl_hours = {
            MemoryLevel.L1_HOT: self.config.l1_ttl,
            MemoryLevel.L2_WARM: self.config.l2_ttl,
            MemoryLevel.L3_VECTOR: self.config.l3_ttl
        }
        
        ttl = ttl_hours.get(level, 24.0)
        return datetime.utcnow() + timedelta(hours=ttl)
    
    async def _get_promotion_reason(self, fragment: MemoryFragment, 
                                   access_pattern: AccessPattern, should_promote: bool) -> str:
        """Формирует причину решения о продвижении"""
        if should_promote:
            reasons = []
            if access_pattern.frequency >= self.config.promotion_threshold:
                reasons.append(f"высокая частота доступа ({access_pattern.frequency})")
            if access_pattern.importance_score >= self.config.importance_threshold:
                reasons.append(f"высокая важность ({access_pattern.importance_score:.2f})")
            if fragment.priority >= 0.6:
                reasons.append(f"высокий приоритет ({fragment.priority:.2f})")
            
            return f"Продвижение: {', '.join(reasons)}"
        else:
            return "Продвижение не требуется"
    
    def _get_cached_decision(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получает закэшированное решение"""
        cached = self._decision_cache.get(cache_key)
        if cached:
            # Проверяем TTL кэша
            if (datetime.utcnow() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached
            else:
                # Удаляем устаревший кэш
                del self._decision_cache[cache_key]
        
        return None
    
    def _cache_decision(self, cache_key: str, decision: Dict[str, Any]):
        """Кэширует решение"""
        self._decision_cache[cache_key] = decision
        
        # Ограничиваем размер кэша
        if len(self._decision_cache) > 1000:
            # Удаляем самые старые записи
            oldest_keys = sorted(
                self._decision_cache.keys(),
                key=lambda k: self._decision_cache[k]["timestamp"]
            )[:100]
            
            for key in oldest_keys:
                del self._decision_cache[key]
    
    def _update_promotion_stats(self, success: bool):
        """Обновляет статистику продвижений"""
        self.promotions_count += 1
        if success:
            self.successful_promotions += 1
        else:
            self.failed_promotions += 1
        
        self.last_promotion = datetime.utcnow()
