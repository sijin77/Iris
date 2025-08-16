"""
Главный файл FastAPI приложения для агента Ириска.
Теперь содержит только инициализацию и подключение роутеров.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Импортируем модели и инициализацию БД
from agent.models import init_db, init_iriska_profile, create_default_agent_templates

# Импортируем роутеры
from routes import include_routers

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# СОЗДАНИЕ FASTAPI ПРИЛОЖЕНИЯ
# ============================================================================

app = FastAPI(
    title="Ириска AI Agent API",
    description="API для AI агента Ириска с поддержкой множественных агентов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# НАСТРОЙКА CORS
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Frontend порт
        "http://127.0.0.1:3000",     # Frontend альтернативный
        "http://frontend:80"          # Docker network
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# ============================================================================

include_routers(app)

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ СТАРТЕ
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Выполняется при запуске приложения.
    Инициализирует базу данных и создает профили агентов.
    """
    try:
        logger.info("🚀 Запуск API Ириски...")
        
        # Инициализируем базу данных
        if init_db():
            logger.info("✅ База данных инициализирована")
            
            # Создаем профиль Ириски
            if init_iriska_profile():
                logger.info("✅ Профиль Ириски создан")
            else:
                logger.warning("⚠️ Профиль Ириски уже существует")
            
            # Создаем шаблоны агентов
            if create_default_agent_templates():
                logger.info("✅ Шаблоны агентов созданы")
            else:
                logger.warning("⚠️ Шаблоны агентов уже существуют")
        else:
            logger.error("❌ Ошибка инициализации базы данных")
            
        logger.info("🎉 API Ириски запущен успешно!")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        raise

# ============================================================================
# КОРНЕВОЙ ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """
    Корневой endpoint - информация о системе.
    """
    return {
        "message": "🚀 Ириска AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "description": "AI агент Ириска с поддержкой множественных агентов"
    }

# ============================================================================
# ВСЕ ENDPOINTS ПЕРЕМЕЩЕНЫ В ОТДЕЛЬНЫЕ МОДУЛИ В ПАПКЕ routes/
# ============================================================================

# Все endpoints перемещены в соответствующие модули в папке routes/

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    # Получаем настройки из переменных окружения
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Запуск сервера на {host}:{port}")
    
    # Запускаем uvicorn сервер
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 