# app/domain/entities.py
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Link:
    short_code: str
    long_url: str
    created_at: datetime
