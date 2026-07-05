from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Document Models ──────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: str
    has_notes: bool = False


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class ExamNotesResponse(BaseModel):
    document_id: str
    filename: str
    notes: dict | list | None = None
    status: str
    message: str = ""


# ── Chat Models ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    document_id: str
    message: str
    chat_history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    language: str = "en"


# ── Reference Search Models ─────────────────────────────────────

class SearchRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)


class ReferenceResult(BaseModel):
    title: str
    description: str
    url: str
    source_type: str = "web"


class SearchResponse(BaseModel):
    topic: str
    results: list[ReferenceResult]
    total: int


# ── Teach-It-Back Models ──────────────────────────────────────────

class TeachItBackRequest(BaseModel):
    document_id: str
    topic: str
    student_explanation: str

class TeachItBackResponse(BaseModel):
    rights: list[str]
    wrongs: list[str]
    missing: list[str]
    model_answer: str
    score: int
    message: str

# ── Feedback Models ───────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    session_id: str
    feature_type: str
    reference_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None

# ── Error Models ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
