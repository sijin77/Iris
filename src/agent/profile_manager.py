import logging
from agent.models import SessionLocal, AgentProfile

logger = logging.getLogger(__name__)

# TODO (profile_manager):
# - Персистентность активных профилей (сохранение/восстановление между рестартами)
# - Потокобезопасность/многопоточность, TTL для кэша
# - API для перечисления профилей и явной установки профиля
# - Правила выбора профиля по контексту/каналу/проекту
# - Тесты: смена профиля, гонки, default fallback

class ActiveProfileStore:
    """Singleton для хранения активных профилей пользователей в памяти."""
    _instance = None
    _profiles = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, user_id):
        return self._profiles.get(user_id)

    def set(self, user_id, profile):
        self._profiles[user_id] = profile

active_profiles = ActiveProfileStore()

def get_agent_profile(session, agent_id=1):
    try:
        return session.query(AgentProfile).filter(AgentProfile.id == agent_id).first()
    except Exception as e:
        logger.exception(f"Ошибка получения профиля агента: {e}")
        return None 