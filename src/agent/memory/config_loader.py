"""
Сервис для загрузки конфигурации суммаризации из БД и профилей агентов.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from agent.models_extended import AgentSummarizationSettings
from agent.memory.summarization_config import SummarizationConfig, DEFAULT_SUMMARIZATION_CONFIG

logger = logging.getLogger(__name__)


class SummarizationConfigLoader:
    """
    Загрузчик конфигурации суммаризации для агентов.
    Обеспечивает загрузку персонализированных настроек из БД.
    """
    
    def __init__(self, db_session: Session):
        """
        Инициализация загрузчика конфигурации
        
        Args:
            db_session: Сессия базы данных
        """
        self.db_session = db_session
        self._cache = {}  # Кэш конфигураций для быстрого доступа
        logger.info("SummarizationConfigLoader initialized")
    
    def get_agent_config(self, agent_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Получает конфигурацию суммаризации для конкретного агента
        
        Args:
            agent_name: Имя агента
            use_cache: Использовать кэш для ускорения
            
        Returns:
            Словарь конфигурации
        """
        # Проверяем кэш
        if use_cache and agent_name in self._cache:
            logger.debug(f"Using cached config for agent: {agent_name}")
            return self._cache[agent_name]
        
        try:
            # Загружаем из БД
            settings = self.db_session.query(AgentSummarizationSettings).filter(
                AgentSummarizationSettings.agent_name == agent_name
            ).first()
            
            if settings:
                config = settings.to_config_dict()
                logger.info(f"Loaded custom config for agent: {agent_name}")
            else:
                # Используем конфигурацию по умолчанию
                config = self._get_default_config()
                logger.info(f"Using default config for agent: {agent_name}")
            
            # Кэшируем результат
            if use_cache:
                self._cache[agent_name] = config
            
            return config
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading config for agent {agent_name}: {e}")
            return self._get_default_config()
        
        except Exception as e:
            logger.error(f"Unexpected error loading config for agent {agent_name}: {e}")
            return self._get_default_config()
    
    def create_agent_config(self, agent_name: str, config: Dict[str, Any]) -> bool:
        """
        Создает новую конфигурацию суммаризации для агента
        
        Args:
            agent_name: Имя агента
            config: Словарь конфигурации
            
        Returns:
            True если успешно создано, False иначе
        """
        try:
            # Проверяем, не существует ли уже конфигурация
            existing = self.db_session.query(AgentSummarizationSettings).filter(
                AgentSummarizationSettings.agent_name == agent_name
            ).first()
            
            if existing:
                logger.warning(f"Config for agent {agent_name} already exists")
                return False
            
            # Создаем новую запись
            settings = AgentSummarizationSettings.from_config_dict(agent_name, config)
            self.db_session.add(settings)
            self.db_session.commit()
            
            # Обновляем кэш
            self._cache[agent_name] = config
            
            logger.info(f"Created new config for agent: {agent_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating config for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error creating config for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
    
    def update_agent_config(self, agent_name: str, config: Dict[str, Any]) -> bool:
        """
        Обновляет конфигурацию суммаризации для агента
        
        Args:
            agent_name: Имя агента
            config: Новая конфигурация
            
        Returns:
            True если успешно обновлено, False иначе
        """
        try:
            settings = self.db_session.query(AgentSummarizationSettings).filter(
                AgentSummarizationSettings.agent_name == agent_name
            ).first()
            
            if not settings:
                # Создаем новую запись если не существует
                return self.create_agent_config(agent_name, config)
            
            # Обновляем существующую запись
            self._update_settings_from_config(settings, config)
            settings.version += 1  # Увеличиваем версию
            
            self.db_session.commit()
            
            # Обновляем кэш
            self._cache[agent_name] = config
            
            logger.info(f"Updated config for agent: {agent_name} (version {settings.version})")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating config for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error updating config for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
    
    def update_agent_patterns(self, agent_name: str, pattern_type: str, patterns: list) -> bool:
        """
        Обновляет конкретные паттерны для агента
        
        Args:
            agent_name: Имя агента
            pattern_type: Тип паттерна (topic_shift, importance_high, etc.)
            patterns: Новые паттерны
            
        Returns:
            True если успешно обновлено, False иначе
        """
        try:
            settings = self.db_session.query(AgentSummarizationSettings).filter(
                AgentSummarizationSettings.agent_name == agent_name
            ).first()
            
            if not settings:
                logger.warning(f"No config found for agent {agent_name}")
                return False
            
            # Обновляем конкретные паттерны
            if pattern_type == "topic_shift":
                settings.topic_shift_patterns = patterns
            elif pattern_type == "questions":
                settings.question_patterns = patterns
            elif pattern_type == "completion":
                settings.completion_patterns = patterns
            elif pattern_type == "temporal_absolute":
                settings.temporal_absolute_markers = patterns
            elif pattern_type == "temporal_relative":
                settings.temporal_relative_markers = patterns
            elif pattern_type == "importance_high":
                settings.high_importance_keywords = patterns
            elif pattern_type == "importance_medium":
                settings.medium_importance_keywords = patterns
            elif pattern_type == "context_shift":
                settings.context_shift_markers = patterns
            elif pattern_type == "technical_context":
                settings.technical_context_markers = patterns
            elif pattern_type == "emotional_context":
                settings.emotional_context_markers = patterns
            else:
                logger.warning(f"Unknown pattern type: {pattern_type}")
                return False
            
            settings.version += 1
            self.db_session.commit()
            
            # Сбрасываем кэш для этого агента
            self._cache.pop(agent_name, None)
            
            logger.info(f"Updated {pattern_type} patterns for agent: {agent_name}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating patterns for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error updating patterns for agent {agent_name}: {e}")
            self.db_session.rollback()
            return False
    
    def get_user_mode_config(self, agent_name: str, mode: str) -> Dict[str, Any]:
        """
        Получает конфигурацию для конкретного режима пользователя
        
        Args:
            agent_name: Имя агента
            mode: Режим пользователя (casual, detailed, technical, etc.)
            
        Returns:
            Словарь конфигурации для режима
        """
        base_config = self.get_agent_config(agent_name)
        user_modes = base_config.get("user_modes", {})
        
        if mode in user_modes:
            # Объединяем базовую конфигурацию с настройками режима
            mode_config = base_config.copy()
            mode_overrides = user_modes[mode]
            
            # Применяем переопределения режима
            for key, value in mode_overrides.items():
                if key == "chunking_strategy":
                    mode_config["chunking_strategy"] = value
                elif key == "max_chunk_size":
                    mode_config["max_chunk_size"] = value
                elif key == "max_context_length":
                    mode_config["max_context_length"] = value
                elif key == "importance_threshold":
                    mode_config["thresholds"]["high_importance"] = value
            
            logger.debug(f"Applied mode '{mode}' config for agent {agent_name}")
            return mode_config
        
        logger.debug(f"Mode '{mode}' not found, using base config for agent {agent_name}")
        return base_config
    
    def clear_cache(self, agent_name: Optional[str] = None):
        """
        Очищает кэш конфигураций
        
        Args:
            agent_name: Имя агента для очистки (None для всех)
        """
        if agent_name:
            self._cache.pop(agent_name, None)
            logger.debug(f"Cleared cache for agent: {agent_name}")
        else:
            self._cache.clear()
            logger.debug("Cleared all config cache")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию по умолчанию"""
        return {
            "enabled": True,
            "chunking_strategy": "hybrid",
            "max_chunk_size": 512,
            "min_chunk_size": 100,
            "overlap_size": 50,
            "max_context_length": 2000,
            "retrieval_k": 8,
            "final_k": 4,
            "thresholds": {
                "high_importance": 0.8,
                "medium_importance": 0.5,
                "min_relevance": 0.2,
                "time_gap": 300
            },
            "weights": {
                "ranking": {"relevance": 0.7, "temporal": 0.2, "importance": 0.1},
                "temporal": {"very_recent": 1.0, "recent": 0.8, "medium": 0.6, "old": 0.4},
                "importance": {
                    "high_keywords": 0.3, "medium_keywords": 0.15,
                    "message_length": 0.1, "question_marks": 0.1,
                    "exclamation_marks": 0.05, "caps_ratio": 0.05, "user_feedback": 0.25
                }
            },
            "patterns": {
                "topic_shift": [
                    r"кстати|by the way|а еще|теперь о|давай поговорим",
                    r"другой вопрос|другая тема|переходим к"
                ],
                "questions": [
                    r"как\s+(?:дела|настроение|ты|вы)",
                    r"что\s+(?:думаешь|скажешь|посоветуешь)"
                ],
                "importance_high": [
                    "важно", "срочно", "критично", "проблема", "ошибка"
                ],
                "importance_medium": [
                    "вопрос", "как", "почему", "что", "когда", "где"
                ],
                "dialogue": {
                    "question_answer": r"(.*?)(?:пользователь:|user:)(.*?)(?:ответ:|answer:)(.*?)(?=пользователь:|user:|$)",
                    "topic_discussion": r"(.*?)(?:говорили о|обсуждали|про|about)(.*?)(?=\.|!|\?|$)"
                }
            },
            "user_modes": {
                "casual": {"chunking_strategy": "size_based", "max_chunk_size": 256},
                "detailed": {"chunking_strategy": "hybrid", "max_chunk_size": 512},
                "technical": {"chunking_strategy": "topic_based", "max_chunk_size": 768}
            }
        }
    
    def _update_settings_from_config(self, settings: AgentSummarizationSettings, config: Dict[str, Any]):
        """Обновляет объект настроек из словаря конфигурации"""
        settings.enabled = config.get("enabled", settings.enabled)
        settings.chunking_strategy = config.get("chunking_strategy", settings.chunking_strategy)
        settings.max_chunk_size = config.get("max_chunk_size", settings.max_chunk_size)
        settings.min_chunk_size = config.get("min_chunk_size", settings.min_chunk_size)
        settings.overlap_size = config.get("overlap_size", settings.overlap_size)
        settings.max_context_length = config.get("max_context_length", settings.max_context_length)
        settings.retrieval_k = config.get("retrieval_k", settings.retrieval_k)
        settings.final_k = config.get("final_k", settings.final_k)
        
        # Обновляем пороги
        thresholds = config.get("thresholds", {})
        settings.high_importance_threshold = thresholds.get("high_importance", settings.high_importance_threshold)
        settings.medium_importance_threshold = thresholds.get("medium_importance", settings.medium_importance_threshold)
        settings.min_relevance_score = thresholds.get("min_relevance", settings.min_relevance_score)
        settings.time_gap_threshold = thresholds.get("time_gap", settings.time_gap_threshold)
        
        # Обновляем веса
        weights = config.get("weights", {})
        if "ranking" in weights:
            settings.ranking_weights = weights["ranking"]
        if "temporal" in weights:
            settings.temporal_weights = weights["temporal"]
        if "importance" in weights:
            settings.importance_weights = weights["importance"]
        
        # Обновляем паттерны
        patterns = config.get("patterns", {})
        if "topic_shift" in patterns:
            settings.topic_shift_patterns = patterns["topic_shift"]
        if "questions" in patterns:
            settings.question_patterns = patterns["questions"]
        if "completion" in patterns:
            settings.completion_patterns = patterns["completion"]
        # ... и так далее для всех паттернов
        
        # Обновляем режимы пользователей
        if "user_modes" in config:
            settings.user_modes = config["user_modes"]


# Глобальный экземпляр загрузчика (будет инициализирован при запуске приложения)
_config_loader: Optional[SummarizationConfigLoader] = None


def initialize_config_loader(db_session: Session):
    """Инициализирует глобальный загрузчик конфигурации"""
    global _config_loader
    _config_loader = SummarizationConfigLoader(db_session)
    logger.info("Global SummarizationConfigLoader initialized")


def get_config_loader() -> Optional[SummarizationConfigLoader]:
    """Получает глобальный загрузчик конфигурации"""
    return _config_loader


def get_agent_summarization_config(agent_name: str, user_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Удобная функция для получения конфигурации суммаризации агента
    
    Args:
        agent_name: Имя агента
        user_mode: Режим пользователя (опционально)
        
    Returns:
        Словарь конфигурации
    """
    if _config_loader:
        if user_mode:
            return _config_loader.get_user_mode_config(agent_name, user_mode)
        else:
            return _config_loader.get_agent_config(agent_name)
    else:
        logger.warning("Config loader not initialized, using default config")
        return SummarizationConfigLoader(None)._get_default_config()
