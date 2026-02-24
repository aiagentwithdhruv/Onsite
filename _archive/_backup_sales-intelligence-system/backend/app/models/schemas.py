"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional


# --- Auth ---
class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    team: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


# --- Leads ---
class LeadResponse(BaseModel):
    id: str
    company: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    stage: Optional[str] = None
    deal_value: Optional[float] = None
    industry: Optional[str] = None
    geography: Optional[str] = None
    assigned_rep_id: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    # Enriched fields from joins
    score: Optional[str] = None
    score_numeric: Optional[int] = None
    score_reason: Optional[str] = None
    days_since_activity: Optional[int] = None


class LeadActionRequest(BaseModel):
    action: str  # called, not_reachable, meeting_scheduled, won, lost
    notes: Optional[str] = None


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int
    page: int
    per_page: int


# --- Research ---
class ResearchResponse(BaseModel):
    lead_id: str
    status: str  # in_progress, complete, failed
    company_info: Optional[dict] = None
    web_research: Optional[str] = None
    notes_summary: Optional[str] = None
    pain_points: Optional[list[str]] = None
    objections: Optional[list[str]] = None
    close_strategy: Optional[str] = None
    talking_points: Optional[list[str]] = None
    similar_deals: Optional[list] = None
    pricing_suggestion: Optional[str] = None
    researched_at: Optional[datetime] = None


# --- Briefs ---
class BriefResponse(BaseModel):
    id: str
    rep_id: str
    brief_content: str
    priority_list: list
    lead_count: Optional[int] = None
    hot_count: Optional[int] = None
    stale_count: Optional[int] = None
    brief_date: date
    created_at: Optional[datetime] = None


# --- Alerts ---
class AlertResponse(BaseModel):
    id: str
    alert_type: str
    message: str
    channel: str
    lead_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered: bool = False
    read_at: Optional[datetime] = None


# --- Analytics ---
class RepPerformance(BaseModel):
    rep_id: str
    rep_name: str
    team: Optional[str] = None
    total_leads: int = 0
    won: int = 0
    lost: int = 0
    calls_this_week: int = 0
    conversion_rate: Optional[float] = 0
    revenue_won: float = 0


class PipelineFunnel(BaseModel):
    stage: str
    count: int
    total_value: float


class SourceAnalysis(BaseModel):
    source: str
    total: int
    won: int
    lost: int
    conversion_rate: float
    total_value: float


# --- Admin ---
class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str
    team: Optional[str] = None
    phone: Optional[str] = None
    zoho_user_id: Optional[str] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    team_lead_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    zoho_user_id: Optional[str] = None


class SyncStatusResponse(BaseModel):
    module: str
    last_sync_at: Optional[datetime] = None
    records_synced: int = 0
    status: str = "unknown"
    sync_type: str = "delta"


class AIUsageSummary(BaseModel):
    period: str
    total_calls: int
    total_cost_usd: float
    by_agent: dict
    by_model: dict
