"""
Системные роуты для API Ириски.
Включает health check, version, статус системы.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

# TODO: Реализовать импорт agent_switcher
# from agent.agent_switcher import agent_switcher

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Проверка здоровья системы.
    """
    try:
        # TODO: Реализовать проверку базы данных
        # from agent.models import SessionLocal
        # from sqlalchemy import text
        # with SessionLocal() as session:
        #     session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "current_agent": "Ириска"  # TODO: Реализовать получение текущего агента
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.get("/version")
async def get_version():
    """
    Получение версии API.
    """
    return {
        "version": "1.0.0",
        "build_date": "2025-08-16",
        "features": [
            "Множественные агенты",
            "Система переключения",
            "Управление профилями",
            "Чат с контекстом"
        ]
    }

@router.get("/status")
async def get_system_status():
    """
    Получает общий статус системы.
    """
    try:
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": "running",
                "database": "connected",
                "llm_server": "connected",
                "current_agent": "Ириска"  # TODO: Реализовать получение текущего агента
            }
        }
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
