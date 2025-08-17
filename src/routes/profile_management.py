"""
API endpoints для управления профилями и их персистентным хранилищем.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from agent.profile_persistence import get_profile_persistence_service
from agent.emotional_memory.profile_corrector_integrated import get_integrated_profile_corrector
from agent.emotional_memory import get_emotional_integration

router = APIRouter()

# Pydantic модели для API

class ProfileChangeRequest(BaseModel):
    agent_name: str
    field_name: str
    old_value: Any
    new_value: Any
    change_reason: str = "manual"
    feedback_text: Optional[str] = None
    confidence_score: float = 1.0
    auto_apply: bool = False

class FeedbackProcessRequest(BaseModel):
    user_id: str
    feedback_text: str
    conversation_context: Optional[List[str]] = None
    agent_name: str = "iriska"

class ProfileSnapshotRequest(BaseModel):
    agent_name: str
    snapshot_type: str = "manual"
    trigger_event: Optional[str] = None
    description: Optional[str] = None

class RollbackRequest(BaseModel):
    agent_name: str
    to_snapshot_id: Optional[int] = None
    hours_back: Optional[int] = None

# ============================================================================
# ENDPOINTS ДЛЯ УПРАВЛЕНИЯ ПРОФИЛЯМИ
# ============================================================================

@router.post("/profiles/changes/save")
async def save_profile_change(request: ProfileChangeRequest):
    """Сохраняет изменение профиля в БД"""
    try:
        persistence_service = get_profile_persistence_service()
        
        change = await persistence_service.save_profile_change(
            agent_name=request.agent_name,
            user_id="system",  # TODO: получать из контекста аутентификации
            field_name=request.field_name,
            old_value=request.old_value,
            new_value=request.new_value,
            change_reason=request.change_reason,
            feedback_text=request.feedback_text,
            confidence_score=request.confidence_score,
            auto_apply=request.auto_apply
        )
        
        if change:
            return {
                "status": "success",
                "change_id": change.id,
                "created_at": change.created_at.isoformat(),
                "auto_applied": change.auto_applied
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save profile change")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profiles/changes/{change_id}/apply")
async def apply_profile_change(change_id: int):
    """Применяет сохраненное изменение профиля"""
    try:
        persistence_service = get_profile_persistence_service()
        
        success = await persistence_service.apply_profile_change(change_id)
        
        if success:
            return {
                "status": "success",
                "change_id": change_id,
                "applied_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to apply profile change")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles/{agent_name}/changes")
async def get_profile_changes(
    agent_name: str,
    user_id: Optional[str] = None,
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000)
):
    """Получает историю изменений профиля"""
    try:
        persistence_service = get_profile_persistence_service()
        
        changes = await persistence_service.get_profile_change_history(
            agent_name=agent_name,
            user_id=user_id,
            days_back=days_back,
            limit=limit
        )
        
        # Конвертируем в JSON-сериализуемый формат
        changes_data = []
        for change in changes:
            changes_data.append({
                "id": change.id,
                "user_id": change.user_id,
                "field_name": change.field_name,
                "old_value": change.old_value,
                "new_value": change.new_value,
                "change_reason": change.change_reason,
                "feedback_text": change.feedback_text,
                "confidence_score": change.confidence_score,
                "emotion_detected": change.emotion_detected,
                "emotion_intensity": change.emotion_intensity,
                "created_at": change.created_at.isoformat(),
                "applied_at": change.applied_at.isoformat() if change.applied_at else None,
                "status": change.status,
                "auto_applied": change.auto_applied
            })
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "total_changes": len(changes_data),
            "changes": changes_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profiles/snapshots/create")
async def create_profile_snapshot(request: ProfileSnapshotRequest):
    """Создает снимок профиля"""
    try:
        persistence_service = get_profile_persistence_service()
        
        snapshot = await persistence_service.create_profile_snapshot(
            agent_name=request.agent_name,
            snapshot_type=request.snapshot_type,
            trigger_event=request.trigger_event,
            description=request.description
        )
        
        if snapshot:
            return {
                "status": "success",
                "snapshot_id": snapshot.id,
                "created_at": snapshot.created_at.isoformat(),
                "snapshot_type": snapshot.snapshot_type
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create profile snapshot")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles/{agent_name}/snapshots")
async def get_profile_snapshots(
    agent_name: str,
    snapshot_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Получает список снимков профиля"""
    try:
        persistence_service = get_profile_persistence_service()
        
        snapshots = await persistence_service.get_profile_snapshots(
            agent_name=agent_name,
            snapshot_type=snapshot_type,
            limit=limit
        )
        
        snapshots_data = []
        for snapshot in snapshots:
            snapshots_data.append({
                "id": snapshot.id,
                "snapshot_type": snapshot.snapshot_type,
                "trigger_event": snapshot.trigger_event,
                "description": snapshot.description,
                "created_at": snapshot.created_at.isoformat(),
                "total_changes": snapshot.total_changes,
                "performance_score": snapshot.performance_score
            })
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "total_snapshots": len(snapshots_data),
            "snapshots": snapshots_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profiles/rollback")
async def rollback_profile(request: RollbackRequest):
    """Откатывает профиль к предыдущему состоянию"""
    try:
        persistence_service = get_profile_persistence_service()
        
        to_datetime = None
        if request.hours_back:
            to_datetime = datetime.utcnow() - timedelta(hours=request.hours_back)
        
        success = await persistence_service.rollback_profile_changes(
            agent_name=request.agent_name,
            to_snapshot_id=request.to_snapshot_id,
            to_datetime=to_datetime
        )
        
        if success:
            return {
                "status": "success",
                "agent_name": request.agent_name,
                "rollback_completed_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Rollback operation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles/{agent_name}/evolution")
async def analyze_profile_evolution(
    agent_name: str,
    days_back: int = Query(30, ge=1, le=365)
):
    """Анализирует эволюцию профиля"""
    try:
        persistence_service = get_profile_persistence_service()
        
        analysis = await persistence_service.analyze_profile_evolution(
            agent_name=agent_name,
            days_back=days_back
        )
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINTS ДЛЯ ЭМОЦИОНАЛЬНОЙ ОБРАТНОЙ СВЯЗИ
# ============================================================================

@router.post("/feedback/process")
async def process_emotional_feedback(request: FeedbackProcessRequest):
    """Обрабатывает эмоциональную обратную связь с автоматической корректировкой профиля"""
    try:
        corrector = get_integrated_profile_corrector()
        
        result = await corrector.process_feedback_with_persistence(
            user_id=request.user_id,
            feedback_text=request.feedback_text,
            conversation_context=request.conversation_context,
            agent_name=request.agent_name
        )
        
        return {
            "status": "success",
            "processing_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/{user_id}/history")
async def get_user_feedback_history(
    user_id: str,
    agent_name: str = "iriska",
    days_back: int = Query(7, ge=1, le=90)
):
    """Получает историю обратной связи пользователя"""
    try:
        corrector = get_integrated_profile_corrector()
        
        history = await corrector.load_adjustment_history(
            user_id=user_id,
            agent_name=agent_name,
            days_back=days_back
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "agent_name": agent_name,
            "total_adjustments": len(history),
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/pending-changes")
async def get_pending_profile_changes(agent_name: str = "iriska"):
    """Получает изменения профиля, ожидающие применения"""
    try:
        corrector = get_integrated_profile_corrector()
        
        pending_changes = await corrector.get_pending_changes(agent_name=agent_name)
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "total_pending": len(pending_changes),
            "pending_changes": pending_changes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/apply-pending/{change_id}")
async def apply_pending_profile_change(change_id: int):
    """Применяет ожидающее изменение профиля"""
    try:
        corrector = get_integrated_profile_corrector()
        
        result = await corrector.apply_pending_change(change_id)
        
        if result.get("status") == "success":
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/rollback/{agent_name}")
async def rollback_recent_feedback_changes(
    agent_name: str,
    hours_back: int = Query(24, ge=1, le=168)
):
    """Откатывает недавние изменения от эмоциональной обратной связи"""
    try:
        corrector = get_integrated_profile_corrector()
        
        result = await corrector.rollback_recent_changes(
            agent_name=agent_name,
            hours_back=hours_back
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/effectiveness/{agent_name}")
async def analyze_feedback_effectiveness(
    agent_name: str,
    days_back: int = Query(30, ge=7, le=365)
):
    """Анализирует эффективность обратной связи"""
    try:
        corrector = get_integrated_profile_corrector()
        
        evolution = await corrector.analyze_profile_evolution(
            agent_name=agent_name,
            days_back=days_back
        )
        
        return {
            "status": "success",
            "agent_name": agent_name,
            "period_days": days_back,
            "effectiveness_analysis": evolution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINTS ДЛЯ СТАТИСТИКИ И МОНИТОРИНГА
# ============================================================================

@router.get("/stats/persistence")
async def get_persistence_stats():
    """Получает статистику работы системы персистентности"""
    try:
        persistence_service = get_profile_persistence_service()
        corrector = get_integrated_profile_corrector()
        
        stats = {
            "persistence_service": persistence_service.get_service_stats(),
            "integrated_corrector": corrector.get_integrated_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(90, ge=30, le=365)):
    """Очищает старые данные профилей"""
    try:
        persistence_service = get_profile_persistence_service()
        
        cleanup_result = await persistence_service.cleanup_old_data(days_to_keep)
        
        return {
            "status": "success",
            "cleanup_result": cleanup_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Проверка здоровья системы управления профилями"""
    try:
        persistence_service = get_profile_persistence_service()
        corrector = get_integrated_profile_corrector()
        emotional_integration = get_emotional_integration()
        
        health_status = {
            "persistence_service": "healthy",
            "integrated_corrector": "healthy", 
            "emotional_integration": "healthy" if emotional_integration else "not_initialized",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Проверяем доступность БД
        try:
            persistence_service.get_db_session().execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception:
            health_status["database"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in health_status.values() if status != health_status["timestamp"]
        ) else "degraded"
        
        return {
            "status": overall_status,
            "components": health_status
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
