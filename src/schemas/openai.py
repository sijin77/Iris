# TODO (schemas):
# - Поддержка attachments (файлы): filename, mimetype, content/text, size
# - Совместимость с OpenAI tool calling (tools/functions)
# - Валидация границ: max_tokens, длина messages

from pydantic import BaseModel
from typing import List, Dict, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = 1024
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    object: str
    choices: List[Dict]
    usage: Dict 