"""
Базовые интерфейсы для компонентов системы памяти как кэш-системы.
Определяет контракты для Promoter, Demoter и Evictor.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import MemoryFragment, AccessPattern, ActivityScore, MemoryLevel, MemoryStats


class IMemoryComponent(ABC):
    """Базовый интерфейс для всех компонентов памяти"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Инициализация компонента"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Завершение работы компонента"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики компонента"""
        pass


class IDataPromoter(IMemoryComponent):
    """Интерфейс для продвижения данных на более высокие уровни"""
    
    @abstractmethod
    async def analyze_promotion_candidates(self, level: MemoryLevel) -> List[MemoryFragment]:
        """Анализирует кандидатов для продвижения с указанного уровня"""
        pass
    
    @abstractmethod
    async def should_promote(self, fragment: MemoryFragment, access_pattern: AccessPattern) -> bool:
        """Определяет, нужно ли продвигать фрагмент"""
        pass
    
    @abstractmethod
    async def promote_fragment(self, fragment: MemoryFragment, target_level: MemoryLevel) -> bool:
        """Продвигает фрагмент на указанный уровень"""
        pass
    
    @abstractmethod
    async def batch_promote(self, fragments: List[MemoryFragment]) -> Dict[str, bool]:
        """Пакетное продвижение фрагментов"""
        pass


class IDataDemoter(IMemoryComponent):
    """Интерфейс для понижения данных на более низкие уровни"""
    
    @abstractmethod
    async def analyze_demotion_candidates(self, level: MemoryLevel) -> List[MemoryFragment]:
        """Анализирует кандидатов для понижения с указанного уровня"""
        pass
    
    @abstractmethod
    async def should_demote(self, fragment: MemoryFragment, activity_score: ActivityScore) -> bool:
        """Определяет, нужно ли понижать фрагмент"""
        pass
    
    @abstractmethod
    async def demote_fragment(self, fragment: MemoryFragment, target_level: MemoryLevel) -> bool:
        """Понижает фрагмент на указанный уровень"""
        pass
    
    @abstractmethod
    async def batch_demote(self, fragments: List[MemoryFragment]) -> Dict[str, bool]:
        """Пакетное понижение фрагментов"""
        pass


class IDataEvictor(IMemoryComponent):
    """Интерфейс для удаления и архивирования данных"""
    
    @abstractmethod
    async def find_expired_fragments(self, level: MemoryLevel) -> List[MemoryFragment]:
        """Находит просроченные фрагменты на указанном уровне"""
        pass
    
    @abstractmethod
    async def should_evict(self, fragment: MemoryFragment, activity_score: ActivityScore) -> bool:
        """Определяет, нужно ли удалять фрагмент"""
        pass
    
    @abstractmethod
    async def evict_fragment(self, fragment: MemoryFragment, reason: str) -> bool:
        """Удаляет фрагмент с указанием причины"""
        pass
    
    @abstractmethod
    async def archive_fragment(self, fragment: MemoryFragment) -> bool:
        """Архивирует фрагмент в долгосрочное хранилище"""
        pass
    
    @abstractmethod
    async def batch_evict(self, fragments: List[MemoryFragment]) -> Dict[str, bool]:
        """Пакетное удаление фрагментов"""
        pass


class IMemoryAnalyzer(IMemoryComponent):
    """Интерфейс для анализа паттернов доступа и активности"""
    
    @abstractmethod
    async def analyze_access_pattern(self, fragment_id: str, user_id: str) -> AccessPattern:
        """Анализирует паттерн доступа к фрагменту"""
        pass
    
    @abstractmethod
    async def calculate_activity_score(self, fragment: MemoryFragment) -> ActivityScore:
        """Вычисляет оценку активности фрагмента"""
        pass
    
    @abstractmethod
    async def get_fragment_importance(self, fragment: MemoryFragment) -> float:
        """Определяет важность фрагмента"""
        pass
    
    @abstractmethod
    async def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Анализирует паттерны пользователя"""
        pass


class IMemoryOptimizer(IMemoryComponent):
    """Интерфейс для оптимизации системы памяти"""
    
    @abstractmethod
    async def optimize_level_distribution(self) -> Dict[MemoryLevel, int]:
        """Оптимизирует распределение данных по уровням"""
        pass
    
    @abstractmethod
    async def balance_levels(self) -> Dict[MemoryLevel, int]:
        """Балансирует уровни памяти"""
        pass
    
    @abstractmethod
    async def cleanup_orphaned_data(self) -> int:
        """Очищает "осиротевшие" данные"""
        pass
    
    @abstractmethod
    async def defragment_level(self, level: MemoryLevel) -> bool:
        """Дефрагментирует указанный уровень"""
        pass


class IMemoryMonitor(IMemoryComponent):
    """Интерфейс для мониторинга системы памяти"""
    
    @abstractmethod
    async def get_memory_stats(self) -> MemoryStats:
        """Получает общую статистику системы памяти"""
        pass
    
    @abstractmethod
    async def get_level_stats(self, level: MemoryLevel) -> Dict[str, Any]:
        """Получает статистику конкретного уровня"""
        pass
    
    @abstractmethod
    async def monitor_performance(self) -> Dict[str, float]:
        """Мониторит производительность системы"""
        pass
    
    @abstractmethod
    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Обнаруживает аномалии в работе системы"""
        pass
    
    @abstractmethod
    async def generate_report(self, report_type: str) -> str:
        """Генерирует отчет указанного типа"""
        pass


class IMemoryStorage(IMemoryComponent):
    """Интерфейс для работы с хранилищами разных уровней"""
    
    @abstractmethod
    async def store_fragment(self, fragment: MemoryFragment, level: MemoryLevel) -> bool:
        """Сохраняет фрагмент на указанном уровне"""
        pass
    
    @abstractmethod
    async def retrieve_fragment(self, fragment_id: str, level: MemoryLevel) -> Optional[MemoryFragment]:
        """Извлекает фрагмент с указанного уровня"""
        pass
    
    @abstractmethod
    async def move_fragment(self, fragment: MemoryFragment, from_level: MemoryLevel, to_level: MemoryLevel) -> bool:
        """Перемещает фрагмент между уровнями"""
        pass
    
    @abstractmethod
    async def delete_fragment(self, fragment_id: str, level: MemoryLevel) -> bool:
        """Удаляет фрагмент с указанного уровня"""
        pass
    
    @abstractmethod
    async def get_level_capacity(self, level: MemoryLevel) -> Dict[str, Any]:
        """Получает информацию о емкости уровня"""
        pass
    
    @abstractmethod
    async def get_level_usage(self, level: MemoryLevel) -> Dict[str, Any]:
        """Получает информацию об использовании уровня"""
        pass
