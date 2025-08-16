# FastAPI + LangChain/LangGraph Custom Agent

## Структура проекта

- `src/`
  - `main.py` — Точка входа FastAPI
  - `api/`
    - `openai_api.py` — Реализация OpenAI-совместимого endpoint
  - `agent/`
    - `core.py` — Логика агента (интерфейс для LangChain/LangGraph)
    - `memory.py` — Кастомная память (опционально)
    - `emotions.py` — Эмоциональный анализ (опционально)
  - `config/`
    - `settings.py` — Конфигурация проекта
  - `schemas/`
    - `openai.py` — Pydantic-схемы для OpenAI API
  - `requirements.txt` — Зависимости

---

## Кратко
- Все запросы идут через `/v1/chat/completions` (OpenAI API).
- Вся логика агента инкапсулирована в `agent/`.
- Можно легко расширять память, эмоции, интеграции. 