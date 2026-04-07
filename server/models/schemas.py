from typing import Optional, List
from pydantic import BaseModel


class ServerInfo(BaseModel):
    id: str
    label: str
    emoji: str
    location: str
    flag: str
    ip: str
    description: str
    why_it_matters: str
    good_ping_ms: int
    ok_ping_ms: int
    category: str


class CategoryInfo(BaseModel):
    id: str
    label: str
    emoji: str
    description: str
    servers: List[ServerInfo]


class ServersResponse(BaseModel):
    categories: List[CategoryInfo]


class SourceInfo(BaseModel):
    id: str
    label: str
    emoji: str
    description: str
    long_description: str
    available: bool
    location: Optional[str]


class SourcesResponse(BaseModel):
    sources: List[SourceInfo]


class HopInfo(BaseModel):
    hop: int
    ip: str
    hostname: str
    label: str
    description: str
    long_description: str
    emoji: str
    city: str
    country: str
    flag: str
    ms: float
    status: str
    fun_fact: str


class TracerouteResponse(BaseModel):
    target: str
    source: str
    total_ms: float
    hops: List[HopInfo]


class PingResult(BaseModel):
    server_id: str
    ms: float
    jitter_ms: float
    packet_loss_pct: float
    status: str
    score: int
    verdict: str
    verdict_long: str


class PingMultiSummary(BaseModel):
    gaming_score: int
    streaming_score: int
    work_score: int
    overall_score: int
    best_server: str
    worst_server: str


class PingMultiResponse(BaseModel):
    source: str
    results: List[PingResult]
    summary: PingMultiSummary


class PingSingleResponse(BaseModel):
    source: str
    result: PingResult


class AIAlternative(BaseModel):
    source_id: str
    label: str
    predicted_ping_ms: float
    confidence: float
    reason: str


class ModelInfo(BaseModel):
    algorithm: str
    training_samples: int
    last_trained: str
    features_used: List[str]


class AIRecommendation(BaseModel):
    model_config = {"protected_namespaces": ()}

    use_case: str
    best_source: str
    best_source_label: str
    confidence: float
    predicted_ping_ms: float
    reason: str
    reason_long: str
    alternatives: List[AIAlternative]
    model_info: ModelInfo
