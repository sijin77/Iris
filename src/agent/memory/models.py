"""
Модели данных для архитектуры памяти как кэш-системы.
Включает фрагменты памяти, паттерны доступа и метаданные.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class MemoryLevel(str, Enum):
    """Уровни памяти в системе"""
    L1_HOT = "L1"      # Redis - горячий кэш
    L2_WARM = "L2"     # SQLite - теплое хранилище
    L3_VECTOR = "L3"   # ChromaDB - векторное хранилище
    L4_COLD = "L4"     # S3/DB - холодный архив


class FragmentType(str, Enum):
    """Типы фрагментов памяти"""
    DIALOGUE = "dialogue"      # Диалоговое сообщение
    CONTEXT = "context"        # Контекстная информация
    EMOTION = "emotion"        # Эмоциональное состояние
    SUMMARY = "summary"        # Суммаризированный контент
    TRIGGER = "trigger"        # Триггерное событие


class MemoryFragment(BaseModel):
    """Фрагмент памяти с метаданными"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="Основное содержимое фрагмента")
    response: Optional[str] = Field(None, description="Ответ агента (если есть)")
    
    # Метаданные
    user_id: str = Field(..., description="ID пользователя")
    fragment_type: FragmentType = Field(..., description="Тип фрагмента")
    emotion: Optional[str] = Field(None, description="Эмоциональное состояние")
    priority: float = Field(0.5, ge=0.0, le=1.0, description="Приоритет фрагмента (0.0-1.0)")
    
    # Временные метки
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Время истечения")
    
    # Уровень памяти
    current_level: MemoryLevel = Field(MemoryLevel.L2_WARM, description="Текущий уровень памяти")
    
    # Статистика доступа
    access_count: int = Field(0, description="Количество обращений")
    access_frequency: float = Field(0.0, description="Частота доступа (обращений в час)")
    
    # Дополнительные метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AccessPattern(BaseModel):
    """Паттерн доступа к фрагменту памяти"""
    
    fragment_id: str = Field(..., description="ID фрагмента")
    user_id: str = Field(..., description="ID пользователя")
    
    # Частота доступа
    frequency: int = Field(0, description="Количество обращений за период")
    hourly_frequency: float = Field(0.0, description="Средняя частота в час")
    daily_frequency: float = Field(0.0, description="Средняя частота в день")
    
    # Недавность использования
    last_access: datetime = Field(default_factory=datetime.utcnow)
    recency_hours: float = Field(0.0, description="Время с последнего доступа в часах")
    
    # Важность
    importance_score: float = Field(0.0, ge=0.0, le=1.0, description="Оценка важности")
    
    # Временные паттерны
    access_times: List[datetime] = Field(default_factory=list, description="Времена доступа")
    peak_hours: List[int] = Field(default_factory=list, description="Часы пиковой активности")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ActivityScore(BaseModel):
    """Оценка активности фрагмента памяти"""
    
    fragment_id: str = Field(..., description="ID фрагмента")
    
    # Основные метрики
    frequency: int = Field(0, description="Общее количество обращений")
    recency: float = Field(0.0, description="Время с последнего доступа в часах")
    importance: float = Field(0.0, ge=0.0, le=1.0, description="Важность фрагмента")
    
    # Производные метрики
    activity_score: float = Field(0.0, description="Общий балл активности")
    hotness_score: float = Field(0.0, description="Оценка 'горячести' данных")
    coldness_score: float = Field(0.0, description="Оценка 'холодности' данных")
    
    # Классификация
    is_hot: bool = Field(False, description="Является ли фрагмент 'горячим'")
    is_warm: bool = Field(False, description="Является ли фрагмент 'теплым'")
    is_cold: bool = Field(False, description="Является ли фрагмент 'холодным'")
    
    def calculate_scores(self):
        """Вычисляет производные метрики"""
        # Общий балл активности (0.0 - 1.0)
        self.activity_score = min(1.0, (self.frequency * 0.4 + 
                                       (1.0 / (1.0 + self.recency)) * 0.4 + 
                                       self.importance * 0.2))
        
        # Оценка "горячести" (0.0 - 1.0)
        self.hotness_score = min(1.0, (self.frequency / 100.0) * 0.6 + 
                                (1.0 / (1.0 + self.recency)) * 0.4)
        
        # Оценка "холодности" (0.0 - 1.0)
        self.coldness_score = min(1.0, (self.recency / 168.0) * 0.7 + 
                                 (1.0 - self.importance) * 0.3)
        
        # Классификация
        self.is_hot = self.hotness_score >= 0.7
        self.is_warm = 0.3 <= self.hotness_score < 0.7
        self.is_cold = self.hotness_score < 0.3


class MemoryConfig(BaseModel):
    """Конфигурация системы памяти"""
    
    # Пороги продвижения
    promotion_threshold: float = Field(0.7, description="Порог для продвижения данных")
    recency_threshold: float = Field(12.0, description="Порог недавности в часах")
    importance_threshold: float = Field(0.5, description="Порог важности для продвижения")
    
    # Пороги понижения
    demotion_threshold: int = Field(5, description="Порог частоты для понижения")
    aging_threshold: float = Field(72.0, description="Порог старения в часах")
    min_importance: float = Field(0.3, description="Минимальная важность для удержания")
    
    # TTL настройки (в часах)
    l1_ttl: float = Field(24.0, description="TTL для L1 (Redis)")
    l2_ttl: float = Field(168.0, description="TTL для L2 (SQLite) - 7 дней")
    l3_ttl: float = Field(720.0, description="TTL для L3 (ChromaDB) - 30 дней")
    
    # Размеры уровней
    l1_max_size: int = Field(10000, description="Максимальный размер L1")
    l2_max_size: int = Field(100000, description="Максимальный размер L2")
    l3_max_size: int = Field(1000000, description="Максимальный размер L3")
    
    # Интервалы оптимизации
    optimization_interval: float = Field(3600.0, description="Интервал оптимизации в секундах")
    cleanup_interval: float = Field(86400.0, description="Интервал очистки в секундах")
    
    # Настройки анализа
    access_history_size: int = Field(100, description="Размер истории доступа")
    frequency_calculation_window: float = Field(24.0, description="Окно расчета частоты в часах")


class MemoryStats(BaseModel):
    """Статистика системы памяти"""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Количество фрагментов по уровням
    l1_count: int = Field(0, description="Количество фрагментов в L1")
    l2_count: int = Field(0, description="Количество фрагментов в L2")
    l3_count: int = Field(0, description="Количество фрагментов в L3")
    l4_count: int = Field(0, description="Количество фрагментов в L4")
    
    # Размеры уровней
    l1_size_bytes: int = Field(0, description="Размер L1 в байтах")
    l2_size_bytes: int = Field(0, description="Размер L2 в байтах")
    l3_size_bytes: int = Field(0, description="Размер L3 в байтах")
    l4_size_bytes: int = Field(0, description="Размер L4 в байтах")
    
    # Статистика операций
    promotions_count: int = Field(0, description="Количество продвижений")
    demotions_count: int = Field(0, description="Количество понижений")
    evictions_count: int = Field(0, description="Количество удалений")
    
    # Производительность
    avg_access_time_ms: float = Field(0.0, description="Среднее время доступа в мс")
    cache_hit_rate: float = Field(0.0, description="Процент попаданий в кэш")
    
    # Ошибки
    error_count: int = Field(0, description="Количество ошибок")
    last_error: Optional[str] = Field(None, description="Последняя ошибка")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
