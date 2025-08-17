"""
Расширенные модели для эмоциональной памяти и персистентного хранения профилей.
Дополняет основные модели из models.py.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, 
    Float, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

# Используем тот же Base что и в основных моделях
from .models import Base

# ============================================================================
# МОДЕЛИ ДЛЯ ПЕРСИСТЕНТНОГО ХРАНЕНИЯ ПРОФИЛЕЙ
# ============================================================================

class ProfileChange(Base):
    """
    Модель для хранения истории изменений профилей агентов.
    Позволяет отслеживать, когда и почему профиль был изменен.
    """
    __tablename__ = "profile_changes"
    
    id = Column(Integer, primary_key=True)
    
    # Связи
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)  # Кто инициировал изменение
    
    # Детали изменения
    field_name = Column(String, nullable=False)  # Какое поле было изменено
    old_value = Column(Text, nullable=True)  # Старое значение
    new_value = Column(Text, nullable=True)  # Новое значение
    
    # Причина и контекст
    change_reason = Column(String, nullable=False)  # feedback, manual, automatic, emotional
    feedback_text = Column(Text, nullable=True)  # Текст обратной связи, если применимо
    confidence_score = Column(Float, default=0.0)  # Уверенность в изменении (0.0-1.0)
    
    # Эмоциональный контекст
    emotion_detected = Column(String, nullable=True)  # Обнаруженная эмоция
    emotion_intensity = Column(Float, default=0.0)  # Интенсивность эмоции
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    applied_at = Column(DateTime, nullable=True)  # Когда изменение было применено
    
    # Статус
    status = Column(String, default="pending")  # pending, applied, reverted, rejected
    auto_applied = Column(Boolean, default=False)  # Было ли применено автоматически
    
    # Метаданные
    metadata = Column(JSON, nullable=True)  # Дополнительные данные в JSON
    
    # Создаем индексы для быстрого поиска
    __table_args__ = (
        Index('idx_profile_changes_agent_user', 'agent_name', 'user_id'),
        Index('idx_profile_changes_created', 'created_at'),
        Index('idx_profile_changes_reason', 'change_reason'),
    )


class ProfileSnapshot(Base):
    """
    Модель для хранения снимков состояния профиля в определенные моменты времени.
    Позволяет откатывать изменения и анализировать эволюцию профиля.
    """
    __tablename__ = "profile_snapshots"
    
    id = Column(Integer, primary_key=True)
    
    # Связи
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False, index=True)
    
    # Снимок профиля
    profile_data = Column(JSON, nullable=False)  # Полный снимок профиля в JSON
    
    # Метаданные снимка
    snapshot_type = Column(String, default="automatic")  # automatic, manual, backup, milestone
    trigger_event = Column(String, nullable=True)  # Что вызвало создание снимка
    description = Column(Text, nullable=True)  # Описание снимка
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Статистика на момент снимка
    total_changes = Column(Integer, default=0)  # Сколько изменений было на момент снимка
    performance_score = Column(Float, nullable=True)  # Оценка производительности профиля
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_profile_snapshots_agent_created', 'agent_name', 'created_at'),
        Index('idx_profile_snapshots_type', 'snapshot_type'),
    )


# ============================================================================
# МОДЕЛИ ДЛЯ ЭМОЦИОНАЛЬНОЙ ПАМЯТИ
# ============================================================================

class EmotionalFragment(Base):
    """
    Модель для хранения эмоциональных фрагментов памяти.
    Расширяет обычные фрагменты памяти эмоциональными данными.
    """
    __tablename__ = "emotional_fragments"
    
    id = Column(Integer, primary_key=True)
    
    # Основные данные
    user_id = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)  # Содержимое фрагмента
    context = Column(Text, nullable=True)  # Контекст разговора
    
    # Эмоциональные характеристики
    emotion_type = Column(String, nullable=False)  # joy, sadness, anger, etc.
    emotion_intensity = Column(Float, default=0.0)  # Интенсивность (0.0-1.0)
    valence = Column(Float, default=0.0)  # Валентность (-1.0 до 1.0)
    arousal = Column(Float, default=0.0)  # Возбуждение (0.0-1.0)
    
    # Нейромодуляторы
    dopamine_level = Column(Float, default=0.0)  # Уровень дофамина
    serotonin_level = Column(Float, default=0.0)  # Уровень серотонина
    norepinephrine_level = Column(Float, default=0.0)  # Уровень норэпинефрина
    
    # Приоритет и важность
    priority = Column(Float, default=0.5)  # Приоритет фрагмента (0.0-1.0)
    emotional_weight = Column(Float, default=0.0)  # Эмоциональный вес
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Статистика доступа
    access_count = Column(Integer, default=0)
    
    # Связи и ассоциации
    related_fragments = Column(JSON, nullable=True)  # ID связанных фрагментов
    
    # Метаданные
    metadata = Column(JSON, nullable=True)
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_emotional_fragments_user_created', 'user_id', 'created_at'),
        Index('idx_emotional_fragments_emotion', 'emotion_type'),
        Index('idx_emotional_fragments_priority', 'priority'),
    )


class EmotionalState(Base):
    """
    Модель для хранения эмоционального состояния пользователя.
    Отслеживает общее настроение и эмоциональную динамику.
    """
    __tablename__ = "emotional_states"
    
    id = Column(Integer, primary_key=True)
    
    # Связи
    user_id = Column(String, nullable=False, index=True)
    
    # Текущее эмоциональное состояние
    dominant_emotion = Column(String, nullable=False)  # Доминирующая эмоция
    emotion_intensity = Column(Float, default=0.0)  # Общая интенсивность
    mood_valence = Column(Float, default=0.0)  # Общая валентность настроения
    
    # Эмоциональная стабильность
    stability_score = Column(Float, default=0.5)  # Стабильность настроения
    volatility = Column(Float, default=0.0)  # Изменчивость эмоций
    
    # Временное окно
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False)
    
    # Статистика периода
    total_interactions = Column(Integer, default=0)
    positive_interactions = Column(Integer, default=0)
    negative_interactions = Column(Integer, default=0)
    
    # Эмоциональный профиль за период
    emotion_distribution = Column(JSON, nullable=True)  # Распределение эмоций
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_emotional_states_user_window', 'user_id', 'window_start', 'window_end'),
        Index('idx_emotional_states_emotion', 'dominant_emotion'),
    )


class FeedbackAnalysis(Base):
    """
    Модель для хранения результатов анализа обратной связи.
    Связывает обратную связь с конкретными изменениями профиля.
    """
    __tablename__ = "feedback_analysis"
    
    id = Column(Integer, primary_key=True)
    
    # Связи
    user_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False)
    profile_change_id = Column(Integer, ForeignKey("profile_changes.id"), nullable=True)
    
    # Исходная обратная связь
    feedback_text = Column(Text, nullable=False)
    conversation_context = Column(JSON, nullable=True)  # Контекст разговора
    
    # Результаты анализа
    feedback_type = Column(String, nullable=False)  # positive, negative, neutral, suggestion
    confidence_score = Column(Float, default=0.0)  # Уверенность в анализе
    
    # Выявленные аспекты для изменения
    target_aspects = Column(JSON, nullable=True)  # Какие аспекты нужно изменить
    suggested_changes = Column(JSON, nullable=True)  # Предлагаемые изменения
    
    # Эмоциональный контекст
    user_emotion = Column(String, nullable=True)
    emotion_intensity = Column(Float, default=0.0)
    
    # Статус обработки
    status = Column(String, default="analyzed")  # analyzed, applied, rejected, pending
    applied_changes = Column(JSON, nullable=True)  # Какие изменения были применены
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_feedback_analysis_user_agent', 'user_id', 'agent_name'),
        Index('idx_feedback_analysis_type', 'feedback_type'),
        Index('idx_feedback_analysis_status', 'status'),
    )


# ============================================================================
# МОДЕЛИ ДЛЯ СИСТЕМЫ ПАМЯТИ L1-L4
# ============================================================================

class MemoryFragment(Base):
    """
    Модель для хранения фрагментов памяти в базе данных (L2 уровень).
    Дополняет Redis-кэш (L1) персистентным хранилищем.
    """
    __tablename__ = "memory_fragments"
    
    id = Column(String, primary_key=True)  # UUID фрагмента
    
    # Основные данные
    user_id = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    fragment_type = Column(String, default="conversation")  # conversation, system, emotional
    
    # Уровень памяти
    memory_level = Column(String, nullable=False, index=True)  # L1, L2, L3, L4
    
    # Приоритет и метрики
    priority = Column(Float, default=0.5)
    importance_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # TTL и жизненный цикл
    ttl_seconds = Column(Integer, nullable=True)  # Time to live
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Метаданные и связи
    metadata = Column(JSON, nullable=True)
    related_fragments = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Статус
    status = Column(String, default="active")  # active, archived, deleted
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_memory_fragments_user_level', 'user_id', 'memory_level'),
        Index('idx_memory_fragments_priority', 'priority'),
        Index('idx_memory_fragments_expires', 'expires_at'),
        Index('idx_memory_fragments_type', 'fragment_type'),
    )


class MemoryOperationLog(Base):
    """
    Модель для логирования операций с памятью.
    Отслеживает продвижения, понижения и удаления фрагментов.
    """
    __tablename__ = "memory_operation_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Связи
    fragment_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Детали операции
    operation_type = Column(String, nullable=False)  # promotion, demotion, eviction, access
    from_level = Column(String, nullable=True)  # Исходный уровень
    to_level = Column(String, nullable=True)  # Целевой уровень
    
    # Причина операции
    reason = Column(String, nullable=True)  # Причина операции
    trigger = Column(String, nullable=True)  # Что вызвало операцию
    
    # Метрики на момент операции
    priority_before = Column(Float, nullable=True)
    priority_after = Column(Float, nullable=True)
    access_count = Column(Integer, default=0)
    
    # Результат операции
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Временная метка
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Создаем индексы
    __table_args__ = (
        Index('idx_memory_ops_fragment_created', 'fragment_id', 'created_at'),
        Index('idx_memory_ops_user_operation', 'user_id', 'operation_type'),
        Index('idx_memory_ops_levels', 'from_level', 'to_level'),
    )


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def create_profile_snapshot(agent_name: str, profile_data: dict, 
                           snapshot_type: str = "automatic", 
                           trigger_event: str = None) -> ProfileSnapshot:
    """Создает снимок профиля"""
    return ProfileSnapshot(
        agent_name=agent_name,
        profile_data=profile_data,
        snapshot_type=snapshot_type,
        trigger_event=trigger_event,
        created_at=datetime.utcnow()
    )


def create_profile_change(agent_name: str, user_id: str, field_name: str,
                         old_value: str, new_value: str, change_reason: str,
                         feedback_text: str = None, confidence_score: float = 0.0,
                         emotion_detected: str = None, emotion_intensity: float = 0.0) -> ProfileChange:
    """Создает запись об изменении профиля"""
    return ProfileChange(
        agent_name=agent_name,
        user_id=user_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        change_reason=change_reason,
        feedback_text=feedback_text,
        confidence_score=confidence_score,
        emotion_detected=emotion_detected,
        emotion_intensity=emotion_intensity,
        created_at=datetime.utcnow()
    )


def create_emotional_fragment(user_id: str, content: str, emotion_type: str,
                            emotion_intensity: float = 0.0, valence: float = 0.0,
                            arousal: float = 0.0, priority: float = 0.5) -> EmotionalFragment:
    """Создает эмоциональный фрагмент"""
    return EmotionalFragment(
        user_id=user_id,
        content=content,
        emotion_type=emotion_type,
        emotion_intensity=emotion_intensity,
        valence=valence,
        arousal=arousal,
        priority=priority,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow()
    )
