"""Typed schemas the LLM must fill. Malformed output is rejected by pydantic."""
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

import config


class ThemeHit(BaseModel):
    theme_id: str
    evidence_span: str = Field(min_length=1)
    severity: int = Field(ge=1, le=3)
    confidence: float = Field(ge=0, le=1)

    @field_validator("theme_id")
    @classmethod
    def known_theme(cls, v: str, info: ValidationInfo) -> str:
        allowed = (info.context or {}).get("theme_ids")
        if allowed is not None and v != "other" and v not in allowed:
            raise ValueError(f"unknown theme_id {v!r}")
        return v


class Extraction(BaseModel):
    record_id: str
    source: str
    sip_status: Literal["stopped", "paused", "continuing", "unclear"]
    sip_status_evidence: str | None = None          # required unless status is unclear
    first_time_investor: Literal["yes", "no", "unclear"]
    first_time_evidence: str | None = None          # required unless unclear
    themes: list[ThemeHit] = []
    one_line_reason: str | None = None

    @field_validator("one_line_reason")
    @classmethod
    def short_reason(cls, v):
        if v and len(v.split()) > config.MAX_ONE_LINE_REASON_WORDS:
            raise ValueError(f"one_line_reason longer than {config.MAX_ONE_LINE_REASON_WORDS} words")
        return v


class FilterItem(BaseModel):
    i: int
    relevant: bool


class OpenCode(BaseModel):
    record_id: str
    reasons: list[dict]  # [{"reason": free text, "quote": verbatim}]
