"""
Расширенные модели для эмоциональной памяти и персистентного хранения профилей.
Дополняет основные модели из models.py.
Включает настройки суммаризации и работы с диалогами.
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
# МОДЕЛИ ДЛЯ НАСТРОЕК СУММАРИЗАЦИИ
# ============================================================================

class AgentSummarizationSettings(Base):
    """
    Модель для хранения настроек суммаризации и работы с диалогами для каждого агента.
    Позволяет персонализировать паттерны и пороги для разных агентов.
    """
    __tablename__ = "agent_summarization_settings"
    
    id = Column(Integer, primary_key=True)
    
    # Связь с профилем агента
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False, unique=True, index=True)
    
    # Основные настройки
    enabled = Column(Boolean, default=True, nullable=False)
    chunking_strategy = Column(String, default="hybrid", nullable=False)  # hybrid, topic_based, etc.
    
    # Параметры чанкинга
    max_chunk_size = Column(Integer, default=512, nullable=False)
    min_chunk_size = Column(Integer, default=100, nullable=False)
    overlap_size = Column(Integer, default=50, nullable=False)
    max_context_length = Column(Integer, default=2000, nullable=False)
    retrieval_k = Column(Integer, default=8, nullable=False)
    final_k = Column(Integer, default=4, nullable=False)
    
    # Пороги важности
    high_importance_threshold = Column(Float, default=0.8, nullable=False)
    medium_importance_threshold = Column(Float, default=0.5, nullable=False)
    min_relevance_score = Column(Float, default=0.2, nullable=False)
    
    # Временные настройки
    time_gap_threshold = Column(Integer, default=300, nullable=False)  # секунды
    
    # Веса для ранжирования (JSON)
    ranking_weights = Column(JSON, default={
        "relevance": 0.7,
        "temporal": 0.2,
        "importance": 0.1
    }, nullable=False)
    
    temporal_weights = Column(JSON, default={
        "very_recent": 1.0,
        "recent": 0.8,
        "medium": 0.6,
        "old": 0.4
    }, nullable=False)
    
    importance_weights = Column(JSON, default={
        "high_keywords": 0.3,
        "medium_keywords": 0.15,
        "message_length": 0.1,
        "question_marks": 0.1,
        "exclamation_marks": 0.05,
        "caps_ratio": 0.05,
        "user_feedback": 0.25
    }, nullable=False)
    
    # Паттерны (JSON массивы)
    topic_shift_patterns = Column(JSON, default=[
        r"кстати|by the way|а еще|теперь о|давай поговорим",
        r"другой вопрос|другая тема|переходим к",
        r"забыл спросить|еще хотел|кстати да",
        r"а что насчет|а как же|а про",
        r"меняя тему|changing topic|new topic"
    ], nullable=False)
    
    question_patterns = Column(JSON, default=[
        r"как\s+(?:дела|настроение|ты|вы)",
        r"что\s+(?:думаешь|скажешь|посоветуешь)",
        r"можешь\s+(?:помочь|рассказать|объяснить)",
        r"расскажи\s+(?:про|о|мне)"
    ], nullable=False)
    
    completion_patterns = Column(JSON, default=[
        r"понятно|ясно|спасибо|thanks|got it",
        r"все ясно|все понял|все поняла",
        r"отлично|хорошо|супер|perfect|great"
    ], nullable=False)
    
    temporal_absolute_markers = Column(JSON, default=[
        r"вчера|сегодня|завтра|послезавтра",
        r"yesterday|today|tomorrow",
        r"на прошлой неделе|на этой неделе|на следующей неделе"
    ], nullable=False)
    
    temporal_relative_markers = Column(JSON, default=[
        r"утром|днем|вечером|ночью",
        r"morning|afternoon|evening|night",
        r"недавно|давно|скоро|потом"
    ], nullable=False)
    
    high_importance_keywords = Column(JSON, default=[
        "важно", "срочно", "критично", "проблема", "ошибка",
        "не работает", "сломалось", "помогите", "help",
        "urgent", "important", "critical", "error", "broken",
        "решение", "вывод", "итог", "conclusion", "result"
    ], nullable=False)
    
    medium_importance_keywords = Column(JSON, default=[
        "вопрос", "как", "почему", "что", "когда", "где",
        "можно", "нужно", "хочу", "планирую", "думаю",
        "question", "how", "why", "what", "when", "where",
        "can", "should", "want", "plan", "think"
    ], nullable=False)
    
    context_shift_markers = Column(JSON, default=[
        r"но\s+(?:сейчас|теперь|давайте)",
        r"однако|however|but now",
        r"с другой стороны|on the other hand",
        r"возвращаясь к|getting back to|back to"
    ], nullable=False)
    
    technical_context_markers = Column(JSON, default=[
        r"код|code|программа|program|скрипт|script",
        r"ошибка|error|баг|bug|исключение|exception",
        r"база данных|database|SQL|запрос|query",
        r"API|REST|HTTP|JSON|XML"
    ], nullable=False)
    
    emotional_context_markers = Column(JSON, default=[
        r"нравится|не нравится|like|dislike",
        r"хорошо|плохо|good|bad|отлично|excellent",
        r"расстроен|радуюсь|грустно|весело",
        r"спасибо|thanks|благодарю|appreciate"
    ], nullable=False)
    
    dialogue_patterns = Column(JSON, default={
        "question_answer": r"(.*?)(?:пользователь:|user:|вопрос:|question:)(.*?)(?:ответ:|answer:|assistant:|агент:)(.*?)(?=пользователь:|user:|$)",
        "topic_discussion": r"(.*?)(?:говорили о|обсуждали|про|about)(.*?)(?=\.|!|\?|$)",
        "problem_solution": r"(.*?)(?:проблема|ошибка|не работает|problem|error)(.*?)(?:решение|исправить|fix|solution)(.*?)(?=\.|!|\?|$)",
        "instruction": r"(.*?)(?:как|how to|инструкция|instruction)(.*?)(?=\.|!|\?|$)",
        "explanation": r"(.*?)(?:объясни|explain|расскажи|tell me)(.*?)(?=\.|!|\?|$)"
    }, nullable=False)
    
    # Режимы пользователей (JSON)
    user_modes = Column(JSON, default={
        "casual": {
            "chunking_strategy": "size_based",
            "max_chunk_size": 256,
            "max_context_length": 1000,
            "importance_threshold": 0.3
        },
        "detailed": {
            "chunking_strategy": "hybrid",
            "max_chunk_size": 512,
            "max_context_length": 2000,
            "importance_threshold": 0.5
        },
        "technical": {
            "chunking_strategy": "topic_based",
            "max_chunk_size": 768,
            "max_context_length": 3000,
            "importance_threshold": 0.7
        }
    }, nullable=False)
    
    # Настройки эмоциональной памяти и нейромодуляции
    emotion_triggers = Column(JSON, default={}, nullable=False)
    neuromodulator_settings = Column(JSON, default={}, nullable=False)
    emotion_analysis_config = Column(JSON, default={}, nullable=False)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Версионирование настроек
    
    # Индексы
    __table_args__ = (
        Index('idx_agent_summarization_agent', 'agent_name'),
        Index('idx_agent_summarization_updated', 'updated_at'),
    )
    
    def to_config_dict(self) -> dict:
        """Преобразует настройки БД в словарь конфигурации"""
        
        # Функция для преобразования списка строк в список объектов с флагом active
        def convert_patterns_to_objects(patterns: list, defaults: list = None) -> list:
            if defaults is None:
                defaults = []
            return [
                {
                    "pattern": pattern,
                    "active": any(default.lower() in pattern.lower() for default in defaults) if defaults else True
                }
                for pattern in (patterns or [])
            ]
        
        # Умные настройки по умолчанию
        smart_defaults = {
            "topic_shift": ["кстати", "другой вопрос", "а еще", "by the way", "speaking of"],
            "questions": ["как дела", "что думаешь", "можешь помочь", "how are you", "what do you think", "can you help"],
            "completion": ["понятно", "спасибо", "отлично", "got it", "thanks", "perfect"],
            "temporal_absolute": ["вчера", "сегодня", "завтра", "yesterday", "today", "tomorrow"],
            "temporal_relative": ["недавно", "скоро", "потом", "recently", "soon", "later"],
            "importance_high": ["важно", "срочно", "проблема", "ошибка", "urgent", "critical", "error", "important"],
            "importance_medium": ["вопрос", "интересно", "думаю", "question", "interesting", "think"],
            "context_shift": ["однако", "с другой стороны", "however", "on the other hand"],
            "technical_context": ["код", "ошибка", "программа", "code", "error", "program"],
            "emotional_context": ["нравится", "хорошо", "плохо", "like", "good", "bad"]
        }
        
        return {
            "agent_name": self.agent_name,
            "enabled": self.enabled,
            "chunking_strategy": self.chunking_strategy,
            "max_chunk_size": self.max_chunk_size,
            "min_chunk_size": self.min_chunk_size,
            "overlap_size": self.overlap_size,
            "max_context_length": self.max_context_length,
            "retrieval_k": self.retrieval_k,
            "final_k": self.final_k,
            "thresholds": {
                "high_importance": self.high_importance_threshold,
                "medium_importance": self.medium_importance_threshold,
                "min_relevance": self.min_relevance_score,
                "time_gap": self.time_gap_threshold
            },
            "weights": {
                "ranking": self.ranking_weights,
                "temporal": self.temporal_weights,
                "importance": self.importance_weights
            },
            "patterns": {
                "topic_shift": convert_patterns_to_objects(self.topic_shift_patterns, smart_defaults["topic_shift"]),
                "questions": convert_patterns_to_objects(self.question_patterns, smart_defaults["questions"]),
                "completion": convert_patterns_to_objects(self.completion_patterns, smart_defaults["completion"]),
                "temporal_absolute": convert_patterns_to_objects(self.temporal_absolute_markers, smart_defaults["temporal_absolute"]),
                "temporal_relative": convert_patterns_to_objects(self.temporal_relative_markers, smart_defaults["temporal_relative"]),
                "importance_high": convert_patterns_to_objects(self.high_importance_keywords, smart_defaults["importance_high"]),
                "importance_medium": convert_patterns_to_objects(self.medium_importance_keywords, smart_defaults["importance_medium"]),
                "context_shift": convert_patterns_to_objects(self.context_shift_markers, smart_defaults["context_shift"]),
                "technical_context": convert_patterns_to_objects(self.technical_context_markers, smart_defaults["technical_context"]),
                "emotional_context": convert_patterns_to_objects(self.emotional_context_markers, smart_defaults["emotional_context"]),
                "dialogue": self.dialogue_patterns
            },
            "user_modes": self.user_modes,
            "emotion_triggers": self.emotion_triggers,
            "neuromodulator_settings": self.neuromodulator_settings,
            "emotion_analysis_config": self.emotion_analysis_config
        }
    
    @classmethod
    def from_config_dict(cls, agent_name: str, config: dict) -> 'AgentSummarizationSettings':
        """Создает экземпляр из словаря конфигурации"""
        
        # Функция для извлечения активных паттернов из объектов
        def extract_active_patterns(pattern_objects: list) -> list:
            if not pattern_objects:
                return []
            
            # Если это уже список строк (старый формат)
            if isinstance(pattern_objects[0], str):
                return pattern_objects
            
            # Если это список объектов с флагом active (новый формат)
            return [obj["pattern"] for obj in pattern_objects if obj.get("active", True)]
        
        patterns = config.get("patterns", {})
        
        return cls(
            agent_name=agent_name,
            enabled=config.get("enabled", True),
            chunking_strategy=config.get("chunking_strategy", "hybrid"),
            max_chunk_size=config.get("max_chunk_size", 512),
            min_chunk_size=config.get("min_chunk_size", 100),
            overlap_size=config.get("overlap_size", 50),
            max_context_length=config.get("max_context_length", 2000),
            retrieval_k=config.get("retrieval_k", 8),
            final_k=config.get("final_k", 4),
            high_importance_threshold=config.get("thresholds", {}).get("high_importance", 0.8),
            medium_importance_threshold=config.get("thresholds", {}).get("medium_importance", 0.5),
            min_relevance_score=config.get("thresholds", {}).get("min_relevance", 0.2),
            time_gap_threshold=config.get("thresholds", {}).get("time_gap", 300),
            ranking_weights=config.get("weights", {}).get("ranking", {}),
            temporal_weights=config.get("weights", {}).get("temporal", {}),
            importance_weights=config.get("weights", {}).get("importance", {}),
            topic_shift_patterns=extract_active_patterns(patterns.get("topic_shift", [])),
            question_patterns=extract_active_patterns(patterns.get("questions", [])),
            completion_patterns=extract_active_patterns(patterns.get("completion", [])),
            temporal_absolute_markers=extract_active_patterns(patterns.get("temporal_absolute", [])),
            temporal_relative_markers=extract_active_patterns(patterns.get("temporal_relative", [])),
            high_importance_keywords=extract_active_patterns(patterns.get("importance_high", [])),
            medium_importance_keywords=extract_active_patterns(patterns.get("importance_medium", [])),
            context_shift_markers=extract_active_patterns(patterns.get("context_shift", [])),
            technical_context_markers=extract_active_patterns(patterns.get("technical_context", [])),
            emotional_context_markers=extract_active_patterns(patterns.get("emotional_context", [])),
            dialogue_patterns=patterns.get("dialogue", {}),
            user_modes=config.get("user_modes", {}),
            emotion_triggers=config.get("emotion_triggers", {}),
            neuromodulator_settings=config.get("neuromodulator_settings", {}),
            emotion_analysis_config=config.get("emotion_analysis_config", {})
        )


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
