"""
API endpoints для управления конфигурацией суммаризации агентов.
Позволяет настраивать паттерны, пороги и параметры чанкинга через REST API.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from agent.memory.config_loader import SummarizationConfigLoader
from agent.models_extended import AgentSummarizationSettings
from config.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PYDANTIC МОДЕЛИ ДЛЯ API
# ============================================================================

class PatternUpdateRequest(BaseModel):
    """Запрос на обновление паттернов"""
    pattern_type: str
    patterns: List[str]


class ThresholdUpdateRequest(BaseModel):
    """Запрос на обновление порогов"""
    high_importance: Optional[float] = None
    medium_importance: Optional[float] = None
    min_relevance: Optional[float] = None
    time_gap: Optional[int] = None


class WeightUpdateRequest(BaseModel):
    """Запрос на обновление весов"""
    ranking: Optional[Dict[str, float]] = None
    temporal: Optional[Dict[str, float]] = None
    importance: Optional[Dict[str, float]] = None


class ChunkingParametersRequest(BaseModel):
    """Запрос на обновление параметров чанкинга"""
    strategy: Optional[str] = None
    max_chunk_size: Optional[int] = None
    min_chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    max_context_length: Optional[int] = None
    retrieval_k: Optional[int] = None
    final_k: Optional[int] = None


class UserModeRequest(BaseModel):
    """Запрос на обновление режима пользователя"""
    mode_name: str
    settings: Dict[str, Any]


class FullConfigRequest(BaseModel):
    """Запрос на полное обновление конфигурации"""
    enabled: Optional[bool] = None
    chunking_strategy: Optional[str] = None
    max_chunk_size: Optional[int] = None
    min_chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None
    max_context_length: Optional[int] = None
    retrieval_k: Optional[int] = None
    final_k: Optional[int] = None
    thresholds: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, Any]] = None
    patterns: Optional[Dict[str, Any]] = None
    user_modes: Optional[Dict[str, Any]] = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config_loader(db: Session = Depends(get_db)) -> SummarizationConfigLoader:
    """Получает загрузчик конфигурации с сессией БД"""
    return SummarizationConfigLoader(db)


def validate_agent_exists(agent_name: str, db: Session):
    """Проверяет существование агента"""
    from agent.models import AgentProfile
    
    agent = db.query(AgentProfile).filter(AgentProfile.name == agent_name).first()
    if not agent:
        raise HTTPException(
            status_code=404, 
            detail=f"Agent '{agent_name}' not found"
        )


def validate_pattern_type(pattern_type: str):
    """Проверяет валидность типа паттерна"""
    valid_types = [
        "topic_shift", "questions", "completion", "temporal_absolute",
        "temporal_relative", "importance_high", "importance_medium",
        "context_shift", "technical_context", "emotional_context"
    ]
    
    if pattern_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pattern type. Must be one of: {', '.join(valid_types)}"
        )


# ============================================================================
# GET ENDPOINTS - Получение конфигурации
# ============================================================================

@router.get("/agents/{agent_name}/config")
async def get_agent_config(
    agent_name: str,
    user_mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получает конфигурацию суммаризации для агента
    
    Args:
        agent_name: Имя агента
        user_mode: Режим пользователя (опционально)
    """
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        
        if user_mode:
            config = config_loader.get_user_mode_config(agent_name, user_mode)
            logger.info(f"Retrieved mode '{user_mode}' config for agent: {agent_name}")
        else:
            config = config_loader.get_agent_config(agent_name)
            logger.info(f"Retrieved base config for agent: {agent_name}")
        
        return {
            "agent_name": agent_name,
            "user_mode": user_mode,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error retrieving config for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/patterns")
async def get_agent_patterns(
    agent_name: str,
    pattern_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получает паттерны агента
    
    Args:
        agent_name: Имя агента
        pattern_type: Тип паттерна (опционально)
    """
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        config = config_loader.get_agent_config(agent_name)
        patterns = config.get("patterns", {})
        
        if pattern_type:
            if pattern_type not in patterns:
                raise HTTPException(
                    status_code=404,
                    detail=f"Pattern type '{pattern_type}' not found"
                )
            
            return {
                "agent_name": agent_name,
                "pattern_type": pattern_type,
                "patterns": patterns[pattern_type]
            }
        
        return {
            "agent_name": agent_name,
            "all_patterns": patterns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving patterns for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}/user-modes")
async def get_agent_user_modes(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """Получает режимы пользователей для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        config = config_loader.get_agent_config(agent_name)
        user_modes = config.get("user_modes", {})
        
        return {
            "agent_name": agent_name,
            "user_modes": user_modes
        }
        
    except Exception as e:
        logger.error(f"Error retrieving user modes for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POST/PUT ENDPOINTS - Создание и обновление конфигурации
# ============================================================================

@router.post("/agents/{agent_name}/config")
async def create_agent_config(
    agent_name: str,
    config_request: FullConfigRequest,
    db: Session = Depends(get_db)
):
    """Создает новую конфигурацию суммаризации для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        
        # Преобразуем Pydantic модель в словарь
        config_dict = config_request.dict(exclude_unset=True)
        
        success = config_loader.create_agent_config(agent_name, config_dict)
        
        if not success:
            raise HTTPException(
                status_code=409,
                detail=f"Configuration for agent '{agent_name}' already exists"
            )
        
        logger.info(f"Created new config for agent: {agent_name}")
        
        return {
            "message": f"Configuration created for agent '{agent_name}'",
            "agent_name": agent_name,
            "config": config_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating config for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/config")
async def update_agent_config(
    agent_name: str,
    config_request: FullConfigRequest,
    db: Session = Depends(get_db)
):
    """Обновляет конфигурацию суммаризации для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        
        # Получаем текущую конфигурацию
        current_config = config_loader.get_agent_config(agent_name)
        
        # Объединяем с новыми значениями
        updated_config = current_config.copy()
        update_dict = config_request.dict(exclude_unset=True)
        
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in updated_config:
                # Для вложенных словарей делаем глубокое слияние
                updated_config[key].update(value)
            else:
                updated_config[key] = value
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update configuration for agent '{agent_name}'"
            )
        
        logger.info(f"Updated config for agent: {agent_name}")
        
        return {
            "message": f"Configuration updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "updated_fields": list(update_dict.keys()),
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/patterns")
async def update_agent_patterns(
    agent_name: str,
    pattern_request: PatternUpdateRequest,
    db: Session = Depends(get_db)
):
    """Обновляет паттерны агента"""
    validate_agent_exists(agent_name, db)
    validate_pattern_type(pattern_request.pattern_type)
    
    try:
        config_loader = get_config_loader(db)
        
        success = config_loader.update_agent_patterns(
            agent_name, 
            pattern_request.pattern_type, 
            pattern_request.patterns
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update patterns for agent '{agent_name}'"
            )
        
        logger.info(f"Updated {pattern_request.pattern_type} patterns for agent: {agent_name}")
        
        return {
            "message": f"Patterns updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "pattern_type": pattern_request.pattern_type,
            "patterns": pattern_request.patterns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating patterns for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/thresholds")
async def update_agent_thresholds(
    agent_name: str,
    threshold_request: ThresholdUpdateRequest,
    db: Session = Depends(get_db)
):
    """Обновляет пороги важности для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        current_config = config_loader.get_agent_config(agent_name)
        
        # Обновляем пороги
        thresholds = current_config.get("thresholds", {})
        update_dict = threshold_request.dict(exclude_unset=True)
        thresholds.update(update_dict)
        
        # Обновляем конфигурацию
        updated_config = current_config.copy()
        updated_config["thresholds"] = thresholds
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update thresholds for agent '{agent_name}'"
            )
        
        logger.info(f"Updated thresholds for agent: {agent_name}")
        
        return {
            "message": f"Thresholds updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "updated_thresholds": update_dict,
            "current_thresholds": thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thresholds for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/weights")
async def update_agent_weights(
    agent_name: str,
    weight_request: WeightUpdateRequest,
    db: Session = Depends(get_db)
):
    """Обновляет веса ранжирования для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        current_config = config_loader.get_agent_config(agent_name)
        
        # Обновляем веса
        weights = current_config.get("weights", {})
        update_dict = weight_request.dict(exclude_unset=True)
        
        for weight_type, weight_values in update_dict.items():
            if weight_type in weights:
                weights[weight_type].update(weight_values)
            else:
                weights[weight_type] = weight_values
        
        # Обновляем конфигурацию
        updated_config = current_config.copy()
        updated_config["weights"] = weights
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update weights for agent '{agent_name}'"
            )
        
        logger.info(f"Updated weights for agent: {agent_name}")
        
        return {
            "message": f"Weights updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "updated_weights": update_dict,
            "current_weights": weights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating weights for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/chunking")
async def update_agent_chunking_parameters(
    agent_name: str,
    chunking_request: ChunkingParametersRequest,
    db: Session = Depends(get_db)
):
    """Обновляет параметры чанкинга для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        current_config = config_loader.get_agent_config(agent_name)
        
        # Обновляем параметры чанкинга
        updated_config = current_config.copy()
        update_dict = chunking_request.dict(exclude_unset=True)
        updated_config.update(update_dict)
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update chunking parameters for agent '{agent_name}'"
            )
        
        logger.info(f"Updated chunking parameters for agent: {agent_name}")
        
        return {
            "message": f"Chunking parameters updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "updated_parameters": update_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chunking parameters for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_name}/user-modes/{mode_name}")
async def update_user_mode(
    agent_name: str,
    mode_name: str,
    mode_settings: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Обновляет настройки режима пользователя для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        current_config = config_loader.get_agent_config(agent_name)
        
        # Обновляем режим пользователя
        user_modes = current_config.get("user_modes", {})
        user_modes[mode_name] = mode_settings
        
        updated_config = current_config.copy()
        updated_config["user_modes"] = user_modes
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update user mode for agent '{agent_name}'"
            )
        
        logger.info(f"Updated user mode '{mode_name}' for agent: {agent_name}")
        
        return {
            "message": f"User mode '{mode_name}' updated for agent '{agent_name}'",
            "agent_name": agent_name,
            "mode_name": mode_name,
            "mode_settings": mode_settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user mode for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DELETE ENDPOINTS - Удаление конфигурации
# ============================================================================

@router.delete("/agents/{agent_name}/config")
async def delete_agent_config(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """Удаляет конфигурацию суммаризации для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        settings = db.query(AgentSummarizationSettings).filter(
            AgentSummarizationSettings.agent_name == agent_name
        ).first()
        
        if not settings:
            raise HTTPException(
                status_code=404,
                detail=f"No configuration found for agent '{agent_name}'"
            )
        
        db.delete(settings)
        db.commit()
        
        # Очищаем кэш
        config_loader = get_config_loader(db)
        config_loader.clear_cache(agent_name)
        
        logger.info(f"Deleted config for agent: {agent_name}")
        
        return {
            "message": f"Configuration deleted for agent '{agent_name}'",
            "agent_name": agent_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting config for agent {agent_name}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_name}/user-modes/{mode_name}")
async def delete_user_mode(
    agent_name: str,
    mode_name: str,
    db: Session = Depends(get_db)
):
    """Удаляет режим пользователя для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        current_config = config_loader.get_agent_config(agent_name)
        
        user_modes = current_config.get("user_modes", {})
        
        if mode_name not in user_modes:
            raise HTTPException(
                status_code=404,
                detail=f"User mode '{mode_name}' not found for agent '{agent_name}'"
            )
        
        # Удаляем режим
        del user_modes[mode_name]
        
        updated_config = current_config.copy()
        updated_config["user_modes"] = user_modes
        
        success = config_loader.update_agent_config(agent_name, updated_config)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete user mode for agent '{agent_name}'"
            )
        
        logger.info(f"Deleted user mode '{mode_name}' for agent: {agent_name}")
        
        return {
            "message": f"User mode '{mode_name}' deleted for agent '{agent_name}'",
            "agent_name": agent_name,
            "mode_name": mode_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user mode for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS - Служебные функции
# ============================================================================

@router.post("/agents/{agent_name}/cache/clear")
async def clear_agent_cache(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """Очищает кэш конфигурации для агента"""
    validate_agent_exists(agent_name, db)
    
    try:
        config_loader = get_config_loader(db)
        config_loader.clear_cache(agent_name)
        
        logger.info(f"Cleared cache for agent: {agent_name}")
        
        return {
            "message": f"Cache cleared for agent '{agent_name}'",
            "agent_name": agent_name
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ЭМОЦИОНАЛЬНАЯ ПАМЯТЬ И НЕЙРОМОДУЛЯЦИЯ
# ============================================================================

@router.get("/agents/{agent_name}/emotion-triggers", response_model=Dict[str, Any])
async def get_agent_emotion_triggers(agent_name: str, db: Session = Depends(get_db)):
    """Получает эмоциональные триггеры агента"""
    config_db = db.query(AgentSummarizationSettings).filter_by(agent_name=agent_name).first()
    if not config_db:
        raise HTTPException(status_code=404, detail=f"Summarization config for agent '{agent_name}' not found.")
    
    return config_db.emotion_triggers or {}


@router.put("/agents/{agent_name}/emotion-triggers", response_model=Dict[str, Any])
async def update_agent_emotion_triggers(
    agent_name: str, 
    triggers_update: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """Обновляет эмоциональные триггеры агента"""
    config_db = db.query(AgentSummarizationSettings).filter_by(agent_name=agent_name).first()
    if not config_db:
        raise HTTPException(status_code=404, detail=f"Summarization config for agent '{agent_name}' not found.")
    
    config_db.emotion_triggers = triggers_update
    config_db.updated_at = datetime.utcnow()
    config_db.version += 1
    
    db.add(config_db)
    db.commit()
    db.refresh(config_db)
    clear_config_cache(agent_name)
    
    logger.info(f"Updated emotion triggers for agent {agent_name}")
    return config_db.to_config_dict()


@router.get("/agents/{agent_name}/neuromodulators", response_model=Dict[str, Any])
async def get_agent_neuromodulator_settings(agent_name: str, db: Session = Depends(get_db)):
    """Получает настройки нейромодуляторов агента"""
    config_db = db.query(AgentSummarizationSettings).filter_by(agent_name=agent_name).first()
    if not config_db:
        raise HTTPException(status_code=404, detail=f"Summarization config for agent '{agent_name}' not found.")
    
    return config_db.neuromodulator_settings or {}


@router.put("/agents/{agent_name}/neuromodulators", response_model=Dict[str, Any])
async def update_agent_neuromodulator_settings(
    agent_name: str, 
    neuromodulator_update: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """Обновляет настройки нейромодуляторов агента"""
    config_db = db.query(AgentSummarizationSettings).filter_by(agent_name=agent_name).first()
    if not config_db:
        raise HTTPException(status_code=404, detail=f"Summarization config for agent '{agent_name}' not found.")
    
    config_db.neuromodulator_settings = neuromodulator_update
    config_db.updated_at = datetime.utcnow()
    config_db.version += 1
    
    db.add(config_db)
    db.commit()
    db.refresh(config_db)
    clear_config_cache(agent_name)
    
    logger.info(f"Updated neuromodulator settings for agent {agent_name}")
    return config_db.to_config_dict()


@router.get("/emotion-triggers/presets")
async def get_emotion_trigger_presets():
    """Возвращает предустановленные наборы эмоциональных триггеров"""
    return {
        "presets": {
            "minimal": {
                "joy_triggers": {"happy": 0.7, "good": 0.5, "great": 0.8, "love": 0.9},
                "sadness_triggers": {"sad": 0.7, "bad": 0.5, "terrible": 0.8, "hate": 0.9},
                "anger_triggers": {"angry": 0.8, "mad": 0.8, "furious": 1.0, "annoyed": 0.6},
                "fear_triggers": {"scared": 0.7, "afraid": 0.7, "worried": 0.5, "panic": 1.0}
            },
            "basic": {
                "joy_triggers": {"happy": 0.8, "good": 0.6},
                "sadness_triggers": {"sad": 0.8, "bad": 0.6},
                "anger_triggers": {"angry": 0.8, "mad": 0.8},
                "fear_triggers": {"scared": 0.8, "afraid": 0.8}
            }
        }
    }


@router.get("/patterns/types")
async def get_pattern_types():
    """Возвращает список доступных типов паттернов"""
    return {
        "pattern_types": [
            {
                "name": "topic_shift",
                "description": "Паттерны смены темы разговора"
            },
            {
                "name": "questions",
                "description": "Паттерны вопросов"
            },
            {
                "name": "completion",
                "description": "Паттерны завершения темы"
            },
            {
                "name": "temporal_absolute",
                "description": "Абсолютные временные маркеры"
            },
            {
                "name": "temporal_relative",
                "description": "Относительные временные маркеры"
            },
            {
                "name": "importance_high",
                "description": "Ключевые слова высокой важности"
            },
            {
                "name": "importance_medium",
                "description": "Ключевые слова средней важности"
            },
            {
                "name": "context_shift",
                "description": "Маркеры смены контекста"
            },
            {
                "name": "technical_context",
                "description": "Маркеры технического контекста"
            },
            {
                "name": "emotional_context",
                "description": "Маркеры эмоционального контекста"
            }
        ]
    }


@router.get("/chunking/strategies")
async def get_chunking_strategies():
    """Возвращает список доступных стратегий чанкинга"""
    return {
        "strategies": [
            {
                "name": "disabled",
                "description": "Чанкинг отключен"
            },
            {
                "name": "size_based",
                "description": "Простое разбиение по размеру"
            },
            {
                "name": "topic_based",
                "description": "Разбиение по темам разговора"
            },
            {
                "name": "time_based",
                "description": "Разбиение по временным промежуткам"
            },
            {
                "name": "context_based",
                "description": "Разбиение по смене контекста"
            },
            {
                "name": "importance_based",
                "description": "Разбиение по важности сообщений"
            },
            {
                "name": "hybrid",
                "description": "Гибридный подход (рекомендуется)"
            }
        ]
    }
