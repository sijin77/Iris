"""
Конфигурация системы чанкинга для решения проблемы больших summaries.
"""

from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel


class ChunkingStrategy(Enum):
    """Стратегии чанкинга"""
    DISABLED = "disabled"          # Без чанкинга (текущее состояние)
    SIZE_BASED = "size_based"      # Простое разбиение по размеру
    TOPIC_BASED = "topic_based"    # По темам разговора
    TIME_BASED = "time_based"      # По временным промежуткам
    CONTEXT_BASED = "context_based" # По смене контекста
    IMPORTANCE_BASED = "importance_based" # По важности
    HYBRID = "hybrid"              # Комбинированный подход (рекомендуется)


class ChunkingConfig(BaseModel):
    """Конфигурация системы чанкинга"""
    
    # Основные настройки
    enabled: bool = True
    strategy: ChunkingStrategy = ChunkingStrategy.HYBRID
    
    # Размеры чанков
    max_chunk_size: int = 512      # Максимальный размер чанка в токенах
    min_chunk_size: int = 100      # Минимальный размер чанка
    overlap_size: int = 50         # Размер перекрытия между чанками
    
    # Настройки поиска
    max_context_length: int = 2000 # Максимальная длина итогового контекста
    retrieval_k: int = 8           # Количество чанков для поиска (больше чем обычно)
    final_k: int = 4               # Количество чанков в итоговом контексте
    
    # Временные настройки
    time_gap_threshold: int = 300  # 5 минут - порог временного разрыва
    
    # Настройки важности
    high_importance_threshold: float = 0.8  # Порог высокой важности
    medium_importance_threshold: float = 0.5 # Порог средней важности
    
    # Настройки ранжирования
    relevance_weight: float = 0.7   # Вес релевантности в итоговой оценке
    temporal_weight: float = 0.2    # Вес времени
    importance_weight: float = 0.1  # Вес важности
    
    # Режимы работы для разных пользователей
    user_modes: Dict[str, Dict[str, Any]] = {
        "casual": {
            "max_chunk_size": 256,
            "strategy": ChunkingStrategy.SIZE_BASED,
            "max_context_length": 1000
        },
        "detailed": {
            "max_chunk_size": 512,
            "strategy": ChunkingStrategy.HYBRID,
            "max_context_length": 2000
        },
        "technical": {
            "max_chunk_size": 768,
            "strategy": ChunkingStrategy.TOPIC_BASED,
            "max_context_length": 3000
        }
    }
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """Получает конфигурацию для конкретного режима"""
        return self.user_modes.get(mode, {
            "max_chunk_size": self.max_chunk_size,
            "strategy": self.strategy,
            "max_context_length": self.max_context_length
        })


# Глобальная конфигурация по умолчанию
DEFAULT_CHUNKING_CONFIG = ChunkingConfig()


def get_chunking_config() -> ChunkingConfig:
    """Получает текущую конфигурацию чанкинга"""
    return DEFAULT_CHUNKING_CONFIG


def update_chunking_config(**kwargs) -> ChunkingConfig:
    """Обновляет конфигурацию чанкинга"""
    global DEFAULT_CHUNKING_CONFIG
    
    for key, value in kwargs.items():
        if hasattr(DEFAULT_CHUNKING_CONFIG, key):
            setattr(DEFAULT_CHUNKING_CONFIG, key, value)
    
    return DEFAULT_CHUNKING_CONFIG


# Предустановленные конфигурации для разных сценариев
PRESET_CONFIGS = {
    "performance": ChunkingConfig(
        max_chunk_size=256,
        strategy=ChunkingStrategy.SIZE_BASED,
        max_context_length=1000,
        retrieval_k=6,
        final_k=3
    ),
    
    "balanced": ChunkingConfig(
        max_chunk_size=512,
        strategy=ChunkingStrategy.HYBRID,
        max_context_length=2000,
        retrieval_k=8,
        final_k=4
    ),
    
    "quality": ChunkingConfig(
        max_chunk_size=768,
        strategy=ChunkingStrategy.TOPIC_BASED,
        max_context_length=3000,
        retrieval_k=12,
        final_k=6
    )
}


def apply_preset_config(preset_name: str) -> bool:
    """Применяет предустановленную конфигурацию"""
    global DEFAULT_CHUNKING_CONFIG
    
    if preset_name in PRESET_CONFIGS:
        DEFAULT_CHUNKING_CONFIG = PRESET_CONFIGS[preset_name]
        return True
    
    return False
