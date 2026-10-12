# models.py - typed Pydantic request/response models for every route in
# app/main.py, reused from Week 6/8 with the prompt-versioning fields
# dropped (out of scope for this security-focused week; see README's
# "Ties to Weeks 6-8").

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TriageRequest(BaseModel):
    patient_message: str = Field(min_length=5, max_length=1000)
    county: str = Field(min_length=2, max_length=40)


class TriageResponse(BaseModel):
    urgency: str
    advice: str
    handled_for: str
