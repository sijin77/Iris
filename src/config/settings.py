# TODO (settings):
# - Перевести на pydantic-settings/Env: префикс, валидация, дефолты
# - Развести MEMORY_DB_URL (SQLAlchemy) и MEMORY_DB_FILE (LangChain)
# - Конфиг retriever/RAG, ключи, флаги включения
# - Профили/эмодзи/подпись: вынести в конфиг

# Конфигурация проекта

class Settings:
	OPENAI_COMPATIBLE: bool = True
	AGENT_NAME: str = "CustomAgent"
	# TODO: Добавить другие настройки

settings = Settings() 