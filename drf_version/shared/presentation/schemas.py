from pydantic import BaseModel, Field


class ShortenRequest(BaseModel):
    url: str = Field(..., description="The long URL to shorten")


class ShortenResponse(BaseModel):
    code: str
    short_url: str
