"""
Конфигурационные модели для системы суммаризации и работы с диалогами.
Все паттерны, пороги и настройки выносятся в конфигурацию агента.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ChunkingStrategy(Enum):
    """Стратегии чанкинга диалогов"""
    DISABLED = "disabled"
    SIZE_BASED = "size_based"
    TOPIC_BASED = "topic_based"
    TIME_BASED = "time_based"
    CONTEXT_BASED = "context_based"
    IMPORTANCE_BASED = "importance_based"
    HYBRID = "hybrid"


class TopicShiftPatterns(BaseModel):
    """Паттерны для определения смены темы"""
    
    # Основные паттерны смены темы
    transition_phrases: List[str] = Field(
        default=[
            r"кстати|by the way|а еще|теперь о|давай поговорим",
            r"другой вопрос|другая тема|переходим к",
            r"забыл спросить|еще хотел|кстати да",
            r"а что насчет|а как же|а про",
            r"меняя тему|changing topic|new topic"
        ],
        description="Фразы-маркеры смены темы"
    )
    
    # Вопросительные паттерны
    question_patterns: List[str] = Field(
        default=[
            r"как\s+(?:дела|настроение|ты|вы)",
            r"что\s+(?:думаешь|скажешь|посоветуешь)",
            r"можешь\s+(?:помочь|рассказать|объяснить)",
            r"расскажи\s+(?:про|о|мне)"
        ],
        description="Паттерны вопросов, которые могут начинать новую тему"
    )
    
    # Паттерны завершения темы
    completion_patterns: List[str] = Field(
        default=[
            r"понятно|ясно|спасибо|thanks|got it",
            r"все ясно|все понял|все поняла",
            r"отлично|хорошо|супер|perfect|great"
        ],
        description="Паттерны завершения обсуждения темы"
    )


class TemporalPatterns(BaseModel):
    """Паттерны для работы с временными маркерами"""
    
    # Абсолютные временные маркеры
    absolute_time_markers: List[str] = Field(
        default=[
            r"вчера|сегодня|завтра|послезавтра",
            r"yesterday|today|tomorrow",
            r"на прошлой неделе|на этой неделе|на следующей неделе",
            r"в понедельник|во вторник|в среду|в четверг|в пятницу|в субботу|в воскресенье"
        ],
        description="Абсолютные временные маркеры"
    )
    
    # Относительные временные маркеры
    relative_time_markers: List[str] = Field(
        default=[
            r"утром|днем|вечером|ночью",
            r"morning|afternoon|evening|night",
            r"недавно|давно|скоро|потом",
            r"recently|long ago|soon|later"
        ],
        description="Относительные временные маркеры"
    )
    
    # Временные промежутки
    time_gap_threshold: int = Field(
        default=300,
        description="Порог временного разрыва в секундах (5 минут)"
    )
    
    # Веса для временного ранжирования
    temporal_weights: Dict[str, float] = Field(
        default={
            "very_recent": 1.0,  # < 24 часов
            "recent": 0.8,       # < 7 дней  
            "medium": 0.6,       # < 30 дней
            "old": 0.4           # > 30 дней
        },
        description="Веса для временного ранжирования документов"
    )


class ImportancePatterns(BaseModel):
    """Паттерны для определения важности сообщений"""
    
    # Ключевые слова высокой важности
    high_importance_keywords: List[str] = Field(
        default=[
            "важно", "срочно", "критично", "проблема", "ошибка",
            "не работает", "сломалось", "помогите", "help",
            "urgent", "important", "critical", "error", "broken",
            "решение", "вывод", "итог", "conclusion", "result"
        ],
        description="Ключевые слова высокой важности"
    )
    
    # Ключевые слова средней важности
    medium_importance_keywords: List[str] = Field(
        default=[
            "вопрос", "как", "почему", "что", "когда", "где",
            "можно", "нужно", "хочу", "планирую", "думаю",
            "question", "how", "why", "what", "when", "where",
            "can", "should", "want", "plan", "think"
        ],
        description="Ключевые слова средней важности"
    )
    
    # Пороги важности
    high_importance_threshold: float = Field(
        default=0.8,
        description="Порог высокой важности"
    )
    
    medium_importance_threshold: float = Field(
        default=0.5,
        description="Порог средней важности"
    )
    
    # Веса для расчета важности
    importance_weights: Dict[str, float] = Field(
        default={
            "high_keywords": 0.3,      # Вес ключевых слов высокой важности
            "medium_keywords": 0.15,   # Вес ключевых слов средней важности
            "message_length": 0.1,     # Вес длины сообщения
            "question_marks": 0.1,     # Вес вопросительных знаков
            "exclamation_marks": 0.05, # Вес восклицательных знаков
            "caps_ratio": 0.05,        # Вес заглавных букв
            "user_feedback": 0.25      # Вес обратной связи пользователя
        },
        description="Веса для расчета важности сообщений"
    )


class ContextPatterns(BaseModel):
    """Паттерны для определения смены контекста"""
    
    # Паттерны смены контекста
    context_shift_markers: List[str] = Field(
        default=[
            r"но\s+(?:сейчас|теперь|давайте)",
            r"однако|however|but now",
            r"с другой стороны|on the other hand",
            r"возвращаясь к|getting back to|back to",
            r"кстати говоря|speaking of|by the way"
        ],
        description="Маркеры смены контекста в разговоре"
    )
    
    # Паттерны технического контекста
    technical_context_markers: List[str] = Field(
        default=[
            r"код|code|программа|program|скрипт|script",
            r"ошибка|error|баг|bug|исключение|exception",
            r"база данных|database|SQL|запрос|query",
            r"API|REST|HTTP|JSON|XML",
            r"сервер|server|клиент|client|frontend|backend"
        ],
        description="Маркеры технического контекста"
    )
    
    # Паттерны эмоционального контекста
    emotional_context_markers: List[str] = Field(
        default=[
            r"нравится|не нравится|like|dislike",
            r"хорошо|плохо|good|bad|отлично|excellent",
            r"расстроен|радуюсь|грустно|весело",
            r"angry|happy|sad|excited|frustrated",
            r"спасибо|thanks|благодарю|appreciate"
        ],
        description="Маркеры эмоционального контекста"
    )


class RelevancePatterns(BaseModel):
    """Паттерны для извлечения релевантных частей из документов"""
    
    # Паттерны для извлечения диалогов
    dialogue_patterns: Dict[str, str] = Field(
        default={
            "question_answer": r"(.*?)(?:пользователь:|user:|вопрос:|question:)(.*?)(?:ответ:|answer:|assistant:|агент:)(.*?)(?=пользователь:|user:|$)",
            "topic_discussion": r"(.*?)(?:говорили о|обсуждали|про|about)(.*?)(?=\.|!|\?|$)",
            "problem_solution": r"(.*?)(?:проблема|ошибка|не работает|problem|error)(.*?)(?:решение|исправить|fix|solution)(.*?)(?=\.|!|\?|$)",
            "instruction": r"(.*?)(?:как|how to|инструкция|instruction)(.*?)(?=\.|!|\?|$)",
            "explanation": r"(.*?)(?:объясни|explain|расскажи|tell me)(.*?)(?=\.|!|\?|$)"
        },
        description="Паттерны для извлечения различных типов диалогов"
    )
    
    # Настройки извлечения
    min_relevance_score: float = Field(
        default=0.2,
        description="Минимальный порог релевантности для включения части текста"
    )
    
    max_extraction_length: int = Field(
        default=800,
        description="Максимальная длина извлекаемой части"
    )


class ChunkingParameters(BaseModel):
    """Параметры чанкинга диалогов"""
    
    # Основные настройки
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.HYBRID,
        description="Стратегия чанкинга"
    )
    
    # Размеры чанков
    max_chunk_size: int = Field(
        default=512,
        description="Максимальный размер чанка в токенах"
    )
    
    min_chunk_size: int = Field(
        default=100,
        description="Минимальный размер чанка в токенах"
    )
    
    overlap_size: int = Field(
        default=50,
        description="Размер перекрытия между чанками в токенах"
    )
    
    # Настройки поиска и ранжирования
    max_context_length: int = Field(
        default=2000,
        description="Максимальная длина итогового контекста"
    )
    
    retrieval_k: int = Field(
        default=8,
        description="Количество чанков для первичного поиска"
    )
    
    final_k: int = Field(
        default=4,
        description="Количество чанков в итоговом контексте"
    )
    
    # Веса для ранжирования
    ranking_weights: Dict[str, float] = Field(
        default={
            "relevance": 0.7,     # Семантическая релевантность
            "temporal": 0.2,      # Временная близость
            "importance": 0.1     # Важность сообщений
        },
        description="Веса для ранжирования результатов поиска"
    )


class SummarizationConfig(BaseModel):
    """Полная конфигурация системы суммаризации"""
    
    # Включение/выключение системы
    enabled: bool = Field(
        default=True,
        description="Включена ли система улучшенной суммаризации"
    )
    
    # Паттерны и маркеры
    topic_patterns: TopicShiftPatterns = Field(
        default_factory=TopicShiftPatterns,
        description="Паттерны смены темы"
    )
    
    temporal_patterns: TemporalPatterns = Field(
        default_factory=TemporalPatterns,
        description="Временные паттерны и настройки"
    )
    
    importance_patterns: ImportancePatterns = Field(
        default_factory=ImportancePatterns,
        description="Паттерны важности сообщений"
    )
    
    context_patterns: ContextPatterns = Field(
        default_factory=ContextPatterns,
        description="Паттерны смены контекста"
    )
    
    relevance_patterns: RelevancePatterns = Field(
        default_factory=RelevancePatterns,
        description="Паттерны для извлечения релевантных частей"
    )
    
    # Параметры чанкинга
    chunking: ChunkingParameters = Field(
        default_factory=ChunkingParameters,
        description="Параметры чанкинга диалогов"
    )
    
    # Режимы работы для разных типов пользователей
    user_modes: Dict[str, Dict[str, Any]] = Field(
        default={
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
            },
            "research": {
                "chunking_strategy": "importance_based",
                "max_chunk_size": 1024,
                "max_context_length": 4000,
                "importance_threshold": 0.8
            }
        },
        description="Предустановленные режимы для разных типов пользователей"
    )
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """Получает конфигурацию для конкретного режима пользователя"""
        return self.user_modes.get(mode, self.user_modes["detailed"])
    
    def update_patterns(self, pattern_type: str, patterns: List[str]) -> bool:
        """Обновляет паттерны определенного типа"""
        try:
            if pattern_type == "topic_shift":
                self.topic_patterns.transition_phrases = patterns
            elif pattern_type == "temporal":
                self.temporal_patterns.absolute_time_markers = patterns
            elif pattern_type == "importance_high":
                self.importance_patterns.high_importance_keywords = patterns
            elif pattern_type == "importance_medium":
                self.importance_patterns.medium_importance_keywords = patterns
            elif pattern_type == "context_shift":
                self.context_patterns.context_shift_markers = patterns
            else:
                return False
            return True
        except Exception:
            return False
    
    def get_all_patterns(self) -> Dict[str, List[str]]:
        """Возвращает все паттерны в виде словаря"""
        return {
            "topic_shift": self.topic_patterns.transition_phrases,
            "topic_questions": self.topic_patterns.question_patterns,
            "topic_completion": self.topic_patterns.completion_patterns,
            "temporal_absolute": self.temporal_patterns.absolute_time_markers,
            "temporal_relative": self.temporal_patterns.relative_time_markers,
            "importance_high": self.importance_patterns.high_importance_keywords,
            "importance_medium": self.importance_patterns.medium_importance_keywords,
            "context_shift": self.context_patterns.context_shift_markers,
            "context_technical": self.context_patterns.technical_context_markers,
            "context_emotional": self.context_patterns.emotional_context_markers
        }


# Конфигурация по умолчанию
DEFAULT_SUMMARIZATION_CONFIG = SummarizationConfig()


def get_summarization_config() -> SummarizationConfig:
    """Получает текущую конфигурацию суммаризации"""
    return DEFAULT_SUMMARIZATION_CONFIG


def create_custom_config(**kwargs) -> SummarizationConfig:
    """Создает кастомную конфигурацию суммаризации"""
    return SummarizationConfig(**kwargs)
