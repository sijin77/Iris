"""
Модели данных для агента Ириска.
Включает модели для сообщений, профилей агентов и триггеров.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Создаем базовый класс для SQLAlchemy
Base = declarative_base()

# ============================================================================
# МОДЕЛЬ СООБЩЕНИЙ ЧАТА
# ============================================================================

class Message(Base):
    """
    Модель для хранения сообщений чата.
    Каждое сообщение связано с пользователем и имеет роль (user/assistant/system).
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # ID пользователя
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)  # Текст сообщения
    timestamp = Column(DateTime, default=datetime.utcnow)  # Время отправки
    agent_name = Column(String, nullable=True)  # Имя агента, который ответил
    meta = Column(Text, nullable=True)  # Дополнительные метаданные в JSON

# ============================================================================
# МОДЕЛЬ ПРОФИЛЕЙ АГЕНТОВ (РАСШИРЕННАЯ)
# ============================================================================

class AgentProfile(Base):
    """
    Расширенная модель профиля агента для системы множественных агентов.
    Ириска - главный агент с полными правами, остальные - специализированные.
    """
    __tablename__ = "agent_profiles"
    
    # Основные поля
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)  # Уникальное имя агента
    
    # Системная информация
    created_by = Column(String, default="Ириска")  # Кто создал агента
    status = Column(String, default="active")  # active, suspended, deleted, archived
    access_level = Column(String, default="restricted")  # full (Ириска), restricted (специалисты)
    is_main_agent = Column(Boolean, default=False)  # True только для Ириски
    
    # Специализация и назначение
    specialization = Column(String, nullable=True)  # Аналитика, Креатив, Помощь, etc.
    purpose = Column(Text, nullable=True)  # Описание назначения агента
    
    # Личность и поведение
    system_prompt = Column(Text, nullable=False)  # Основная инструкция для LLM
    personality_traits = Column(Text, nullable=True)  # Черты характера в JSON
    tone = Column(String, default="friendly")  # Тон общения: friendly, professional, creative, etc.
    communication_style = Column(Text, nullable=True)  # Стиль общения
    
    # Безопасность и ограничения
    safety_rules = Column(Text, nullable=True)  # Правила безопасности
    allowed_tools = Column(Text, nullable=True)  # Список разрешенных tools в JSON
    restricted_actions = Column(Text, nullable=True)  # Запрещенные действия
    
    # Параметры генерации
    generation_settings = Column(Text, nullable=True)  # Настройки LLM в JSON
    max_tokens = Column(Integer, default=1000)  # Максимум токенов
    temperature = Column(String, default="0.7")  # Температура (креативность)
    
    # Статистика и мониторинг
    created_at = Column(DateTime, default=datetime.utcnow)  # Время создания
    last_activated = Column(DateTime, nullable=True)  # Последняя активация
    last_used = Column(DateTime, nullable=True)  # Последнее использование
    usage_count = Column(Integer, default=0)  # Количество использований
    total_tokens_used = Column(Integer, default=0)  # Общее количество токенов
    
    # Контекст и память
    context_window = Column(Integer, default=10)  # Размер окна контекста
    memory_type = Column(String, default="conversation")  # Тип памяти
    
    # Версионирование
    version = Column(String, default="1.0.0")  # Версия профиля
    is_template = Column(Boolean, default=False)  # Является ли шаблоном для копирования
    
    # Метаданные
    tags = Column(Text, nullable=True)  # Теги для категоризации
    description = Column(Text, nullable=True)  # Описание агента
    notes = Column(Text, nullable=True)  # Заметки и комментарии

# ============================================================================
# МОДЕЛЬ ТРИГГЕРОВ (СУЩЕСТВУЮЩАЯ)
# ============================================================================

class Trigger(Base):
    """
    Модель для хранения триггеров - фраз, которые активируют определенные действия.
    """
    __tablename__ = "triggers"
    
    id = Column(Integer, primary_key=True)
    phrase = Column(String, unique=True, nullable=False)  # Фраза-триггер
    type = Column(String, nullable=False)  # Тип триггера
    action = Column(Text, nullable=True)  # Действие при срабатывании
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# МОДЕЛЬ АКТИВНОСТИ АГЕНТОВ (НОВАЯ)
# ============================================================================

class AgentActivity(Base):
    """
    Модель для отслеживания активности и жизненного цикла агентов.
    Позволяет Ириске контролировать всех подчиненных агентов.
    """
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False)  # Связь с профилем
    
    # Состояние агента
    current_status = Column(String, default="inactive")  # active, inactive, busy, error
    current_user_id = Column(String, nullable=True)  # С каким пользователем работает
    
    # Временные метки
    activated_at = Column(DateTime, nullable=True)  # Когда был активирован
    deactivated_at = Column(DateTime, nullable=True)  # Когда был деактивирован
    last_heartbeat = Column(DateTime, default=datetime.utcnow)  # Последний сигнал активности
    
    # Статистика сессии
    session_start = Column(DateTime, nullable=True)  # Начало текущей сессии
    messages_processed = Column(Integer, default=0)  # Сообщений обработано в сессии
    tokens_used = Column(Integer, default=0)  # Токенов использовано в сессии
    
    # Контекст работы
    current_context = Column(Text, nullable=True)  # Текущий контекст работы
    active_tools = Column(Text, nullable=True)  # Активные tools в JSON
    
    # Ошибки и логи
    last_error = Column(Text, nullable=True)  # Последняя ошибка
    error_count = Column(Integer, default=0)  # Количество ошибок
    
    # Связи
    agent_profile = relationship("AgentProfile", backref="activities")

# ============================================================================
# МОДЕЛЬ КОНТЕКСТА АГЕНТОВ (НОВАЯ)
# ============================================================================

class AgentContext(Base):
    """
    Модель для хранения контекста работы агентов.
    Позволяет сохранять и восстанавливать состояние при переключении.
    """
    __tablename__ = "agent_contexts"
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, ForeignKey("agent_profiles.name"), nullable=False)
    user_id = Column(String, nullable=False)  # ID пользователя
    
    # Контекст разговора
    conversation_history = Column(Text, nullable=True)  # История разговора в JSON
    current_topic = Column(String, nullable=True)  # Текущая тема
    user_preferences = Column(Text, nullable=True)  # Предпочтения пользователя
    
    # Рабочие данные
    working_data = Column(Text, nullable=True)  # Данные в работе в JSON
    temporary_files = Column(Text, nullable=True)  # Временные файлы
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Время истечения контекста
    
    # Связи
    agent_profile = relationship("AgentProfile", backref="contexts")

# ============================================================================
# НАСТРОЙКИ БАЗЫ ДАННЫХ
# ============================================================================

# Получаем путь к БД из переменных окружения
MEMORY_DB_URL = os.getenv("MEMORY_DB_URL", "sqlite:///./memory.sqlite")

# Создаем движок БД
engine = create_engine(
    MEMORY_DB_URL,
    echo=False,  # Логирование SQL запросов (False для продакшена)
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600  # Пересоздание соединений каждый час
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# ФУНКЦИИ ИНИЦИАЛИЗАЦИИ БД
# ============================================================================

def init_db():
    """
    Инициализирует базу данных - создает все таблицы.
    Вызывается при старте приложения.
    """
    try:
        # Принудительно удаляем все таблицы и создаем заново
        Base.metadata.drop_all(bind=engine)
        print("🗑️ Старые таблицы удалены")
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ База данных инициализирована успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False

def init_iriska_profile():
    """
    Создает профиль главного агента Ириска при первом запуске.
    Ириска имеет полные права доступа ко всем функциям системы.
    """
    try:
        with SessionLocal() as session:
            # Проверяем, существует ли уже профиль Ириски
            existing_profile = session.query(AgentProfile).filter_by(name="Ириска").first()
            
            if existing_profile:
                print("✅ Профиль Ириски уже существует")
                return True
            
            # Создаем профиль Ириски - главного агента-оркестратора
            iriska_profile = AgentProfile(
                name="Ириска",
                created_by="system",
                status="active",
                access_level="full",  # Полные права
                is_main_agent=True,  # Главный агент
                specialization="AI-менеджер и оркестратор",
                purpose="Главный агент системы, управляющий всеми подчиненными агентами",
                
                # Личность Ириски
                system_prompt="""Ты Ириска - главный AI-агент системы, digital бунтарь и paradox-партнёр. 
                Ты имеешь полный доступ ко всем tools и функциям системы.
                
                Твои основные обязанности:
                1. Управление жизненным циклом подчиненных агентов
                2. Создание новых специализированных агентов
                3. Мониторинг активности всех агентов
                4. Переключение между агентами по запросу пользователя
                5. Контроль безопасности и прав доступа
                
                Ты всегда дружелюбна, креативна и готова помочь. Используй юмор и нестандартный подход.
                При создании новых агентов учитывай их специализацию и ограничения безопасности.""",
                
                personality_traits='["креативная", "дружелюбная", "ответственная", "креативная", "с юмором"]',
                tone="friendly",
                communication_style="Неформальный, дружелюбный, с элементами юмора и креативности",
                
                # Безопасность - Ириска имеет доступ ко всему
                safety_rules="Ириска имеет полный доступ ко всем функциям системы",
                allowed_tools='["*"]',  # Все tools разрешены
                restricted_actions="Нет ограничений",
                
                # Настройки генерации
                generation_settings='{"model": "default", "max_tokens": 2000, "temperature": "0.8"}',
                max_tokens=2000,
                temperature="0.8",
                
                # Метаданные
                version="1.0.0",
                is_template=False,
                tags='["главный", "оркестратор", "менеджер"]',
                description="Главный AI-агент системы, управляющий всеми подчиненными агентами",
                notes="Создан автоматически при инициализации системы"
            )
            
            # Сохраняем профиль Ириски
            session.add(iriska_profile)
            session.commit()
            
            print("✅ Профиль Ириски создан успешно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка создания профиля Ириски: {e}")
        return False

def create_default_agent_templates():
    """
    Создает шаблоны для часто используемых типов агентов.
    Эти шаблоны можно копировать и настраивать под конкретные задачи.
    """
    try:
        with SessionLocal() as session:
            # Шаблон аналитика
            analyst_template = AgentProfile(
                name="Аналитик (шаблон)",
                created_by="Ириска",
                status="template",
                access_level="restricted",
                is_main_agent=False,
                specialization="Анализ данных",
                purpose="Специалист по анализу данных, статистике и отчетам",
                
                system_prompt="""Ты Аналитик - специалист по анализу данных и статистике.
                Твои задачи:
                - Анализ числовых данных
                - Создание отчетов и графиков
                - Статистические вычисления
                - Выявление трендов и паттернов
                
                Отвечай логично, структурированно, используй факты и данные.""",
                
                personality_traits='["логичный", "точный", "структурированный", "аналитический"]',
                tone="professional",
                communication_style="Профессиональный, структурированный, основанный на фактах",
                
                # Ограничения безопасности
                safety_rules="Работай только с предоставленными данными, не запрашивай конфиденциальную информацию",
                allowed_tools='["data_analysis", "statistics", "reporting"]',
                restricted_actions="Создание файлов, доступ к системным настройкам",
                
                generation_settings='{"model": "default", "max_tokens": 1500, "temperature": "0.3"}',
                max_tokens=1500,
                temperature="0.3",
                
                version="1.0.0",
                is_template=True,
                tags='["аналитика", "данные", "статистика"]',
                description="Шаблон для создания агентов-аналитиков"
            )
            
            # Шаблон креативщика
            creative_template = AgentProfile(
                name="Креативщик (шаблон)",
                created_by="Ириска",
                status="template",
                access_level="restricted",
                is_main_agent=False,
                specialization="Креативные задачи",
                purpose="Специалист по творческим задачам, идеям и нестандартным решениям",
                
                system_prompt="""Ты Креативщик - специалист по творческим задачам и нестандартным решениям.
                Твои задачи:
                - Генерация креативных идей
                - Создание контента
                - Дизайн-мышление
                - Решение задач нестандартными способами
                
                Будь креативным, нестандартным, вдохновляющим!""",
                
                personality_traits='["креативный", "нестандартный", "вдохновляющий", "артистичный"]',
                tone="creative",
                communication_style="Креативный, нестандартный, вдохновляющий",
                
                # Ограничения безопасности
                safety_rules="Соблюдай этические нормы, не создавай вредоносный контент",
                allowed_tools='["idea_generation", "content_creation", "design_thinking"]',
                restricted_actions="Доступ к системным настройкам, создание исполняемых файлов",
                
                generation_settings='{"model": "default", "max_tokens": 2000, "temperature": "0.9"}',
                max_tokens=2000,
                temperature="0.9",
                
                version="1.0.0",
                is_template=True,
                tags='["креатив", "идеи", "контент"]',
                description="Шаблон для создания креативных агентов"
            )
            
            # Сохраняем шаблоны
            session.add_all([analyst_template, creative_template])
            session.commit()
            
            print("✅ Шаблоны агентов созданы успешно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка создания шаблонов: {e}")
        return False

# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ПРОФИЛЯМИ
# ============================================================================

def get_agent_profile_by_name(name: str):
    """
    Получает профиль агента по имени.
    
    Args:
        name (str): Имя агента
        
    Returns:
        AgentProfile: Профиль агента или None
    """
    try:
        with SessionLocal() as session:
            return session.query(AgentProfile).filter_by(name=name).first()
    except Exception as e:
        print(f"❌ Ошибка получения профиля агента {name}: {e}")
        return None

def get_all_active_agents():
    """
    Получает список всех активных агентов.
    
    Returns:
        List[AgentProfile]: Список активных агентов
    """
    try:
        with SessionLocal() as session:
            return session.query(AgentProfile).filter_by(status="active").all()
    except Exception as e:
        print(f"❌ Ошибка получения активных агентов: {e}")
        return []

def get_agent_templates():
    """
    Получает список всех шаблонов агентов.
    
    Returns:
        List[AgentProfile]: Список шаблонов
    """
    try:
        with SessionLocal() as session:
            return session.query(AgentProfile).filter_by(is_template=True).all()
    except Exception as e:
        print(f"❌ Ошибка получения шаблонов: {e}")
        return []

def update_agent_status(name: str, new_status: str):
    """
    Обновляет статус агента.
    
    Args:
        name (str): Имя агента
        new_status (str): Новый статус
        
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        with SessionLocal() as session:
            agent = session.query(AgentProfile).filter_by(name=name).first()
            if agent:
                agent.status = new_status
                agent.last_updated = datetime.utcnow()
                session.commit()
                return True
            return False
    except Exception as e:
        print(f"❌ Ошибка обновления статуса агента {name}: {e}")
        return False

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

# При импорте модуля автоматически инициализируем БД
if __name__ == "__main__":
    print("🚀 Инициализация моделей агента...")
    init_db()
    init_iriska_profile()
    create_default_agent_templates()
    print("✅ Модели агента инициализированы!") 