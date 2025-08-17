"""
Модели данных для эмоциональной памяти.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ..memory.models import MemoryFragment, MemoryLevel


class EmotionType(str, Enum):
    """Типы эмоций"""
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"
    ANGER = "anger"
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"


class EmotionIntensity(str, Enum):
    """Интенсивность эмоций"""
    VERY_LOW = "very_low"    # 0.0-0.2
    LOW = "low"              # 0.2-0.4
    MEDIUM = "medium"        # 0.4-0.6
    HIGH = "high"            # 0.6-0.8
    VERY_HIGH = "very_high"  # 0.8-1.0


class ModulatorType(str, Enum):
    """Типы нейромодуляторов"""
    DOPAMINE = "dopamine"        # Вознаграждение, мотивация
    SEROTONIN = "serotonin"      # Настроение, удовлетворенность
    NOREPINEPHRINE = "norepinephrine"  # Внимание, стресс
    ACETYLCHOLINE = "acetylcholine"    # Обучение, память
    GABA = "gaba"                # Торможение, расслабление


class EmotionalFragment(BaseModel):
    """Фрагмент памяти с эмоциональными метаданными"""
    
    # Базовый фрагмент памяти
    memory_fragment: MemoryFragment
    
    # Эмоциональные характеристики
    emotion_type: EmotionType
    emotion_intensity: float = Field(ge=0.0, le=1.0, description="Интенсивность эмоции 0-1")
    emotion_confidence: float = Field(ge=0.0, le=1.0, description="Уверенность в определении эмоции")
    
    # Нейромодуляция
    neuro_modulators: Dict[ModulatorType, float] = Field(default_factory=dict)
    emotional_weight: float = Field(ge=0.0, le=1.0, description="Общий эмоциональный вес")
    
    # Связи и контекст
    emotional_links: List[str] = Field(default_factory=list, description="ID связанных эмоциональных фрагментов")
    emotional_tags: List[str] = Field(default_factory=list, description="Эмоциональные теги")
    
    # Временные характеристики
    emotion_detected_at: datetime = Field(default_factory=datetime.now)
    last_emotional_access: Optional[datetime] = None
    emotional_decay_rate: float = Field(default=0.1, description="Скорость эмоционального затухания")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmotionalState(BaseModel):
    """Текущее эмоциональное состояние агента"""
    
    # Основные эмоции
    current_emotions: Dict[EmotionType, float] = Field(default_factory=dict)
    dominant_emotion: EmotionType = EmotionType.NEUTRAL
    overall_valence: float = Field(ge=-1.0, le=1.0, description="Общая валентность (-1 негатив, +1 позитив)")
    arousal_level: float = Field(ge=0.0, le=1.0, description="Уровень возбуждения")
    
    # Нейромодуляторы
    modulator_levels: Dict[ModulatorType, float] = Field(default_factory=dict)
    
    # Контекст
    recent_emotional_events: List[str] = Field(default_factory=list, description="ID недавних эмоциональных событий")
    emotional_context_summary: str = Field(default="", description="Краткое описание эмоционального контекста")
    
    # Временные характеристики
    state_timestamp: datetime = Field(default_factory=datetime.now)
    state_duration: int = Field(default=0, description="Длительность текущего состояния в секундах")
    
    # Статистика
    emotion_history: Dict[str, Any] = Field(default_factory=dict, description="История эмоциональных изменений")


class EmotionalLink(BaseModel):
    """Связь между эмоциональными фрагментами"""
    
    # Основная информация
    id: str = Field(description="Уникальный ID связи")
    source_fragment_id: str = Field(description="ID исходного фрагмента")
    target_fragment_id: str = Field(description="ID целевого фрагмента")
    
    # Характеристики связи
    link_type: str = Field(description="Тип связи (similarity, sequence, contrast)")
    emotional_similarity: float = Field(ge=0.0, le=1.0, description="Эмоциональное сходство")
    link_strength: float = Field(ge=0.0, le=1.0, description="Сила связи")
    
    # Контекст
    created_by: str = Field(description="Как была создана связь (auto, manual, inference)")
    creation_context: str = Field(default="", description="Контекст создания связи")
    
    # Временные характеристики
    created_at: datetime = Field(default_factory=datetime.now)
    last_activated: Optional[datetime] = None
    activation_count: int = Field(default=0, description="Количество активаций связи")
    
    # Метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackAnalysis(BaseModel):
    """Анализ обратной связи от пользователя"""
    
    # Основная информация
    user_id: str
    feedback_text: str
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Анализ настроений
    feedback_emotion: EmotionType
    feedback_intensity: float = Field(ge=0.0, le=1.0)
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Оценка настроения (-1 негатив, +1 позитив)")
    
    # Категоризация обратной связи
    feedback_category: str = Field(description="Категория обратной связи (personality, behavior, response_style)")
    feedback_aspect: str = Field(description="Конкретный аспект (tone, humor, helpfulness, etc.)")
    
    # Контекст
    conversation_context: List[str] = Field(default_factory=list, description="ID сообщений из контекста")
    agent_behavior_context: Dict[str, Any] = Field(default_factory=dict, description="Контекст поведения агента")
    
    # Анализ изменений
    suggested_adjustments: List[str] = Field(default_factory=list, description="Предлагаемые корректировки")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Уверенность в анализе")
    
    # Приоритет
    feedback_priority: float = Field(ge=0.0, le=1.0, description="Приоритет обратной связи")
    requires_immediate_action: bool = Field(default=False)


class ProfileAdjustment(BaseModel):
    """Корректировка профиля агента"""
    
    # Основная информация
    adjustment_id: str
    user_id: str
    profile_field: str = Field(description="Поле профиля для корректировки")
    
    # Изменения
    old_value: Any = Field(description="Старое значение")
    new_value: Any = Field(description="Новое значение")
    adjustment_type: str = Field(description="Тип корректировки (increment, decrement, replace, append)")
    
    # Обоснование
    based_on_feedback: List[str] = Field(default_factory=list, description="ID обратной связи, на основе которой сделана корректировка")
    adjustment_reason: str = Field(description="Причина корректировки")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Уверенность в необходимости корректировки")
    
    # Временные характеристики
    created_at: datetime = Field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Контроль
    is_applied: bool = Field(default=False)
    is_reversible: bool = Field(default=True)
    approval_required: bool = Field(default=False)
    
    # Мониторинг эффективности
    effectiveness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    user_satisfaction_change: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    
    # Метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmotionalMemoryStats(BaseModel):
    """Статистика эмоциональной памяти"""
    
    # Общая статистика
    total_emotional_fragments: int = 0
    total_emotional_links: int = 0
    total_profile_adjustments: int = 0
    
    # Распределение эмоций
    emotion_distribution: Dict[EmotionType, int] = Field(default_factory=dict)
    intensity_distribution: Dict[EmotionIntensity, int] = Field(default_factory=dict)
    
    # Нейромодуляторы
    average_modulator_levels: Dict[ModulatorType, float] = Field(default_factory=dict)
    modulator_activity: Dict[ModulatorType, int] = Field(default_factory=dict)
    
    # Эффективность
    successful_adjustments: int = 0
    failed_adjustments: int = 0
    user_satisfaction_trend: List[float] = Field(default_factory=list)
    
    # Временные характеристики
    stats_period_start: datetime
    stats_period_end: datetime
    last_updated: datetime = Field(default_factory=datetime.now)


class EmotionalMemoryConfig(BaseModel):
    """Конфигурация эмоциональной памяти"""
    
    # Основные настройки
    emotion_detection_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    emotional_weight_multiplier: float = Field(default=1.5, ge=1.0, le=3.0)
    max_emotional_links_per_fragment: int = Field(default=5, ge=1, le=20)
    
    # Нейромодуляция
    dopamine_reward_multiplier: float = Field(default=1.2, ge=1.0, le=2.0)
    serotonin_stability_factor: float = Field(default=0.8, ge=0.1, le=1.0)
    emotional_decay_rate: float = Field(default=0.1, ge=0.01, le=0.5)
    
    # Корректировка профиля
    profile_adjustment_threshold: float = Field(default=0.7, ge=0.5, le=1.0)
    max_adjustments_per_day: int = Field(default=3, ge=1, le=10)
    adjustment_confidence_threshold: float = Field(default=0.6, ge=0.3, le=1.0)
    
    # Обратная связь
    feedback_analysis_depth: int = Field(default=5, ge=3, le=10, description="Глубина анализа контекста")
    minimum_feedback_length: int = Field(default=10, ge=5, le=100)
    
    # Временные настройки
    emotional_memory_ttl_hours: int = Field(default=168, ge=24, le=720, description="TTL эмоциональной памяти в часах (по умолчанию неделя)")
    link_cleanup_interval_hours: int = Field(default=24, ge=1, le=72)
    
    # Производительность
    max_concurrent_analyses: int = Field(default=3, ge=1, le=10)
    batch_processing_size: int = Field(default=10, ge=5, le=50)
