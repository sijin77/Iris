#!/usr/bin/env python3
"""
Главный файл запуска Iriska с полной системой памяти и эмоциональной памятью.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты системы памяти
from agent.memory import EnhancedMemoryController, MemoryConfig
from agent.emotional_memory import (
    initialize_emotional_memory, 
    shutdown_emotional_memory,
    EmotionalMemoryConfig
)

# Импорты основного приложения
from routes.chat import router as chat_router, openai_router
from routes.agents import router as agents_router
from routes.config import router as config_router
from routes.system import router as system_router
from routes.tools import router as tools_router
from routes.profile_management import router as profile_router


# Глобальные экземпляры
enhanced_memory_controller = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global enhanced_memory_controller
    
    try:
        logger.info("🚀 Запуск Iriska с полной системой памяти...")
        
        # 1. Инициализируем расширенный контроллер памяти
        memory_config = MemoryConfig(
            optimization_interval_minutes=30,
            cleanup_interval_minutes=60,
            max_fragments_per_level=10000,
            promotion_threshold=0.7,
            demotion_threshold=0.3,
            eviction_threshold=0.1
        )
        
        enhanced_memory_controller = EnhancedMemoryController(memory_config)
        
        if await enhanced_memory_controller.initialize():
            logger.info("✅ Расширенный контроллер памяти инициализирован")
        else:
            logger.error("❌ Не удалось инициализировать контроллер памяти")
        
        # 2. Инициализируем эмоциональную память
        emotional_config = EmotionalMemoryConfig(
            emotion_detection_threshold=0.3,
            emotional_weight_multiplier=1.5,
            profile_adjustment_threshold=0.7,
            max_adjustments_per_day=3
        )
        
        if await initialize_emotional_memory(enhanced_memory_controller, emotional_config):
            logger.info("✅ Эмоциональная память инициализирована")
        else:
            logger.warning("⚠️ Эмоциональная память не инициализирована")
        
        # 3. Запускаем фоновые процессы оптимизации
        if enhanced_memory_controller:
            await enhanced_memory_controller.start()
            logger.info("✅ Фоновые процессы памяти запущены")
        
        logger.info("🎉 Iriska полностью инициализирована!")
        
        yield
        
    finally:
        logger.info("🔄 Завершение работы Iriska...")
        
        # Останавливаем эмоциональную память
        await shutdown_emotional_memory()
        logger.info("✅ Эмоциональная память остановлена")
        
        # Останавливаем контроллер памяти
        if enhanced_memory_controller:
            await enhanced_memory_controller.stop()
            logger.info("✅ Контроллер памяти остановлен")
        
        logger.info("👋 Iriska завершила работу")


# Создаем приложение FastAPI
app = FastAPI(
    title="Iriska AI Agent",
    description="AI Agent с полной системой памяти и эмоциональной адаптацией",
    version="2.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(openai_router, prefix="/v1", tags=["OpenAI Compatible"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(config_router, prefix="/api/v1/config", tags=["Configuration"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
app.include_router(tools_router, prefix="/api/v1/tools", tags=["Tools"])
app.include_router(profile_router, prefix="/api/v1/profiles", tags=["Profile Management"])


@app.get("/")
async def root():
    """Главная страница"""
    return {
        "message": "Iriska AI Agent v2.0 - Полная система памяти",
        "status": "running",
        "features": [
            "Многоуровневая память L1-L4",
            "Эмоциональная память и адаптация",
            "Автоматическая корректировка профиля",
            "Нейромодуляция приоритетов",
            "Интеграция с LangChain",
            "OpenAI совместимый API"
        ]
    }


@app.get("/api/v1/memory/status")
async def memory_status():
    """Статус системы памяти"""
    if not enhanced_memory_controller:
        return {"status": "not_initialized"}
    
    try:
        stats = await enhanced_memory_controller.get_comprehensive_stats()
        return {
            "status": "active",
            "controller_type": "EnhancedMemoryController",
            "is_running": enhanced_memory_controller.is_running,
            "stats": stats
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/v1/memory/optimize")
async def trigger_optimization():
    """Запускает полный цикл оптимизации памяти"""
    if not enhanced_memory_controller:
        return {"status": "not_initialized"}
    
    try:
        results = await enhanced_memory_controller.run_full_optimization_cycle()
        return {
            "status": "completed",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/v1/memory/emergency")
async def emergency_optimization(target_utilization: float = 0.7):
    """Экстренная оптимизация памяти"""
    if not enhanced_memory_controller:
        return {"status": "not_initialized"}
    
    try:
        results = await enhanced_memory_controller.emergency_optimization(target_utilization)
        return {
            "status": "completed", 
            "results": results
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/v1/memory/rebalance")
async def rebalance_storage():
    """Перебалансировка данных между уровнями"""
    if not enhanced_memory_controller:
        return {"status": "not_initialized"}
    
    try:
        results = await enhanced_memory_controller.rebalance_storage_levels()
        return {
            "status": "completed",
            "results": results
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/v1/emotional/status")
async def emotional_memory_status():
    """Статус эмоциональной памяти"""
    from agent.emotional_memory import get_emotional_integration
    
    integration = get_emotional_integration()
    if not integration:
        return {"status": "not_initialized"}
    
    try:
        stats = integration.get_integration_stats()
        return {
            "status": "active",
            "stats": stats
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/v1/emotional/summary/{user_id}")
async def get_emotional_summary(user_id: str, hours: int = 24):
    """Получает эмоциональную сводку для пользователя"""
    from agent.emotional_memory import get_emotional_integration
    
    integration = get_emotional_integration()
    if not integration:
        return {"status": "not_initialized"}
    
    try:
        summary = await integration.get_emotional_summary_for_user(user_id, hours)
        return {
            "status": "success",
            "user_id": user_id,
            "period_hours": hours,
            "summary": summary
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    # Настройки из переменных окружения
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Запуск Iriska на {host}:{port}")
    
    uvicorn.run(
        "main_with_memory:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
