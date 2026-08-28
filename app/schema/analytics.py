from pydantic import BaseModel
from typing import List, Optional

class StatCard(BaseModel):
    value: float | int
    change_percentage: float
    is_growth: bool
    label: str

class DashboardAnalytics(BaseModel):
    total_participants: StatCard
    active_programs: StatCard
    total_revenue: StatCard
    completion_rate: StatCard

class TrendDataPoint(BaseModel):
    date: str
    participants: int
    revenue: float

class AnalyticsTrendResponse(BaseModel):
    trends: List[TrendDataPoint]
    total_revenue: float
    total_participants: int
    period_label: str
