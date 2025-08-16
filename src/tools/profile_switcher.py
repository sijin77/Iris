import re
from agent.models import SessionLocal, AgentProfile

# TODO (tools:profile_switcher):
# - Конфигурируемые триггеры из БД/конфига, i18n
# - Фаззи-матчинг/синонимы, исключения ложных срабатываний
# - Тесты на покрытие кейсов

def detect_profile_switch(user_message: str) -> str | None:
    """
    Определяет, хочет ли пользователь сменить профиль по ключевым словам.
    Возвращает имя профиля или None.
    """
    triggers = {
        "ириска": "Ириска",
        "деловой": "Деловой",
        "флирт": "Флирт",
        # Добавьте свои триггеры и профили
    }
    for key, profile in triggers.items():
        if re.search(key, user_message, re.IGNORECASE):
            return profile
    return None

def get_profile_by_name(profile_name: str):
    with SessionLocal() as session:
        return session.query(AgentProfile).filter(AgentProfile.name == profile_name).first() 