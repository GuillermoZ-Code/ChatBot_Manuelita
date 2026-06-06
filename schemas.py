from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    numero: str = Field(..., min_length=3, description="Número o identificador de sesión")


class ChatResponse(BaseModel):
    response: str
    numero: str
    chat_id: Optional[int] = None
    route: str = "agent"
    tool_used: str = "none"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    answer: str
    route: str
    tool_used: str = "none"
    metadata: Dict[str, Any] = Field(default_factory=dict)