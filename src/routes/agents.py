"""
Роуты для управления агентами.
Включает создание, переключение, получение информации об агентах.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from typing import Dict, Any

# TODO: Реализовать импорт функций
# from tools.agent_manager import CreateAgentRequest, create_agent_profile
# from agent.agent_switcher import (
#     agent_switcher, switch_to_agent_tool, 
#     return_to_iriska_tool, get_current_agent_tool
# )

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def list_agents():
    """
    Получает список всех доступных агентов.
    """
    try:
        # TODO: Реализовать получение списка агентов
        available_agents = ["Ириска", "Аналитик", "Креативщик"]
        return {
            "status": "success",
            "agents": available_agents,
            "current_agent": "Ириска",  # TODO: Реализовать получение текущего агента
            "total_count": len(available_agents)
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка агентов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current")
async def get_current_agent_info():
    """
    Получает информацию о текущем активном агенте.
    """
    try:
        # TODO: Реализовать получение текущего агента
        current_agent = "Ириска"
        # TODO: Реализовать получение информации об агенте
        agent_info = f"Текущий агент: {current_agent}"
        
        return {
            "status": "success",
            "current_agent": current_agent,
            "info": agent_info,
            "is_iriska": current_agent == "Ириска"
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о текущем агенте: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/switch")
async def switch_agent(agent_name: str, user_id: str = "default"):
    """
    Переключается на указанного агента.
    """
    try:
        # TODO: Реализовать переключение на агента
        result = f"Переключение на агента {agent_name} выполнено"
        
        return {
            "status": "success" if "❌" not in result else "error",
            "message": result,
            "new_agent": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка переключения на агента {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return")
async def return_to_iriska(user_id: str = "default"):
    """
    Возвращается к Ириске (главному агенту).
    """
    try:
        # TODO: Реализовать возврат к Ириске
        result = "Возврат к Ириске выполнен"
        
        return {
            "status": "success" if "❌" not in result else "error",
            "message": result,
            "new_agent": "Ириска",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка возврата к Ириске: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_switch_history(limit: int = 10):
    """
    Получает историю переключений между агентами.
    """
    try:
        # TODO: Реализовать получение истории переключений
        # from agent.agent_switcher import get_switch_history_tool
        # history_text = get_switch_history_tool(limit)
        history_text = f"История переключений (последние {limit}): Переключение на Аналитик, Возврат к Ириске"
        
        return {
            "status": "success",
            "history": history_text,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения истории переключений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_new_agent(request: Dict[str, Any]):
    """
    Создает нового специализированного агента.
    """
    try:
        logger.info(f"🤖 Создание нового агента: {request.get('name', 'Unknown')}")
        
        # TODO: Реализовать создание агента через agent_manager
        # result = create_agent_profile(...)
        result = f"✅ Агент {request.get('name', 'Unknown')} успешно создан"
        
        # Проверяем результат
        if "✅" in result:
            return {
                "status": "success",
                "message": result,
                "agent_name": request.get('name', 'Unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": result,
                "agent_name": request.get('name', 'Unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания агента: {e}")
        raise HTTPException(status_code=500, detail=str(e))
