"""
Модуль эмоциональной памяти для агента Iriska.

Эмоциональная память отвечает за:
- Анализ эмоционального контекста сообщений
- Нейромодуляцию приоритетов фрагментов памяти
- Создание эмоциональных связей между воспоминаниями
- Корректировку профиля агента на основе обратной связи
- Предоставление эмоционального контекста для генерации ответов
"""

from .emotion_analyzer import EmotionAnalyzer, EmotionType, EmotionIntensity
from .neuro_modulator import NeuroModulator, ModulatorType
from .emotional_memory import EmotionalMemory
from .emotional_context import EmotionalContext
from .profile_corrector import ProfileCorrector
from .integration import (
    EmotionalMemoryIntegration, 
    initialize_emotional_memory,
    get_emotional_integration,
    shutdown_emotional_memory
)
from .models import (
    EmotionalFragment,
    EmotionalState,
    EmotionalLink,
    FeedbackAnalysis,
    ProfileAdjustment
)

__all__ = [
    # Основные компоненты
    "EmotionalMemory",
    "EmotionAnalyzer", 
    "NeuroModulator",
    "EmotionalContext",
    "ProfileCorrector",
    
    # Интеграция
    "EmotionalMemoryIntegration",
    "initialize_emotional_memory",
    "get_emotional_integration", 
    "shutdown_emotional_memory",
    
    # Модели данных
    "EmotionalFragment",
    "EmotionalState", 
    "EmotionalLink",
    "FeedbackAnalysis",
    "ProfileAdjustment",
    
    # Енумы
    "EmotionType",
    "EmotionIntensity",
    "ModulatorType"
]

__version__ = "0.1.0"
__description__ = "Emotional memory system for Iriska AI agent"
