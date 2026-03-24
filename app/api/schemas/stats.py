import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel


class SUserActivityResponse(BaseModel):
    period: datetime
    value: int
    user_id: uuid.UUID | str


class SUserRegistrationsResponse(BaseModel):
    period: datetime
    value: int


class SSystemMetricsResponse(BaseModel):
    period: datetime
    total_requests: int
    avg_response_time: float
