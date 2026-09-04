"""
Pydantic models defining the dashboard data contract.

Changes to these models must be reflected in the dashboard specification,
mock data, and pipeline/run.py so all data sources remain consistent.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

class OwnTrendPoint(BaseModel):
    q: str
    revenue: float
    earnings: float

class CompanyCard(BaseModel):
    ticker: str
    name: str
    sector: str
    quarter: str
    status: Literal["new", "seen"]
    verdict: str
    direction: Literal["above", "below", "inline"]
    ownTrend: list[OwnTrendPoint]
    ownAvgGrowth: float
    thisGrowth: float
    sectorPercentile: int
    sectorPeerCount: int
    margin: list[float]
    channel: str
    lastSent: str
    opened: bool
    timeToVerdict: str

class RecentVerdict(BaseModel):
    ticker: str
    verdict: str
    quarter: str
    sentAt: str

class Metrics(BaseModel):
    timeToVerdictAvg: str
    coverageRate: float
    engagementRate: float
    backtestCorrelation: float

class WatchlistResponse(BaseModel):
    companies: list[CompanyCard]
    recentVerdicts: list[RecentVerdict]
    metrics: Metrics
