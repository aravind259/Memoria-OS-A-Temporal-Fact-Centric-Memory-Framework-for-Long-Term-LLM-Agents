from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.container import memory_manager

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    tenant_id: Optional[str] = "default_tenant"
    image_url: Optional[str] = None
    image_b64: Optional[str] = None


@router.post("/chat")
def chat(request: ChatRequest):
    return memory_manager.chat(
        message=request.message,
        user_id=request.user_id or "default_user",
        tenant_id=request.tenant_id or "default_tenant",
        image_url=request.image_url,
        image_b64=request.image_b64
    )