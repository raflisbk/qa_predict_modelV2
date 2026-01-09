from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel


class Recommendation(BaseModel):
    rank: int
    day: str
    time_window: str


class MetaData(BaseModel):
    keyword: str
    source: Literal["live_apify", "cache_fresh", "cache_stale"]
    apify_stats: Optional[Dict[str, Any]] = None


class PredictionResponse(BaseModel):
    status: str
    meta: MetaData
    data: Dict[str, Any]
