from typing import Literal
from pydantic import BaseModel, Field
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


class TeachItBackConceptEvaluation(BaseModel):
    concept: str
    description: str
    importance: str
    source_evidence: str
    weight: int
    status: str
    student_evidence: str
    feedback: str
    points_earned: float


class TeachItBackResponse(BaseModel):
    rights: list[str]
    wrongs: list[str]
    missing: list[str]
    concept_evaluations: list[TeachItBackConceptEvaluation]
    model_answer: str
    score: int
    message: str


# ── Upgrade Me Models ─────────────────────────────────────────────

class UpgradeMeFlowchartRequest(BaseModel):
    document_id: str
    topic: str = Field(..., min_length=1, max_length=200)

class UpgradeMeFlowchartNode(BaseModel):
    id: str
    label: str
    explanation: str
    kind: Literal["start", "concept", "decision", "step", "end"] = "concept"

class UpgradeMeFlowchartEdge(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    label: str = ""

class UpgradeMeFlowchartResponse(BaseModel):
    title: str
    summary: str
    nodes: list[UpgradeMeFlowchartNode]
    edges: list[UpgradeMeFlowchartEdge]

class UpgradeMeQuizRequest(UpgradeMeFlowchartRequest):
    pass

class UpgradeMeQuizQuestion(BaseModel):
    id: str
    type: Literal["multiple_choice", "concept"]
    question: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str

class UpgradeMeQuizResponse(BaseModel):
    topic: str
    questions: list[UpgradeMeQuizQuestion]

class UpgradeMeQuizAnswer(BaseModel):
    question_id: str
    answer: str
    question: str = ""
    type: Literal["multiple_choice", "concept"] = "concept"
    correct_answer: str = ""
    explanation: str = ""

class UpgradeMeQuizEvaluateRequest(UpgradeMeFlowchartRequest):
    answers: list[UpgradeMeQuizAnswer] = Field(default_factory=list)

class UpgradeMeQuizResult(BaseModel):
    question_id: str
    correct: bool
    correct_answer: str
    explanation: str
    feedback: str

class UpgradeMeQuizEvaluateResponse(BaseModel):
    score: int
    total: int
    feedback: str
    results: list[UpgradeMeQuizResult]


# ── Error Models ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
