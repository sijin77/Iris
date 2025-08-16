"""
Инициализация роутеров для API Ириски.
Объединяет все роуты в единую систему.
"""

from fastapi import APIRouter
from . import chat, agents, tools, system, config

# Создаем главный роутер
api_router = APIRouter(prefix="/api", tags=["API"])

# Подключаем все роуты
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])

# Системные роуты (без префикса /api)
system_router = APIRouter(tags=["System"])
system_router.include_router(system.router)

# Роутер для OpenAI совместимости
openai_router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])
openai_router.include_router(chat.openai_router)

def include_routers(app):
    """Подключает все роутеры к приложению"""
    app.include_router(api_router)
    app.include_router(system_router)
    app.include_router(openai_router)
