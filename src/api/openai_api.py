# TODO (api):
# - Streaming: поддержка SSE/WebSocket для по-символьной выдачи
# - Uploads: эндпоинт multipart для файлов и их парсинг
# - /health, /version, CORS/RateLimit/Auth при необходимости
# - Единая ошибка/логирование, request_id для трассировки

from fastapi import APIRouter
from schemas.openai import ChatRequest, ChatResponse
from agent.core import agent_respond
import logging
logger = logging.getLogger(__name__)
from fastapi import HTTPException
from agent.models import SessionLocal, add_trigger, TriggerType
from fastapi import Body
from pydantic import BaseModel

router = APIRouter()
 
@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    try:
        response = await agent_respond(request)
        return response
    except Exception as e:
        logger.exception(f"Ошибка в chat_completions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

class AddTriggerRequest(BaseModel):
    phrase: str
    type: TriggerType

@router.post("/triggers/add")
async def add_trigger_endpoint(request: AddTriggerRequest):
    with SessionLocal() as session:
        success = add_trigger(session, request.phrase, request.type)
        if success:
            return {"status": "ok", "message": f"Триггер '{request.phrase}' (тип: {request.type.value}) успешно добавлен!"}
        else:
            return {"status": "exists", "message": f"Триггер '{request.phrase}' (тип: {request.type.value}) уже существует."} 