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
    sip_status: Literal["stopped", "paused", "reduced", "continuing", "unclear"]
    sip_status_evidence: str | None = None          # required unless status is unclear
    first_time_investor: Literal["yes", "no", "unclear"]
    first_time_evidence: str | None = None          # required unless unclear
    time_since_start: Literal["<1m", "1-6m", "6-12m", ">12m", "unclear"] = "unclear"
    time_since_start_evidence: str | None = None    # required unless unclear
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


class OpenCodeItem(BaseModel):
    question: Literal["start", "behaviour", "stop"]
    code: str = Field(min_length=2, max_length=80)   # short free-text label
    quote: str = Field(min_length=1)                  # verbatim


class OpenCode(BaseModel):
    record_id: str
    codes: list[OpenCodeItem] = []


# ---- Stage 4b: context fields for the brief's remaining questions ----
CheckWhat = Literal["returns_or_value", "nav_or_units", "instalment_status", "portfolio_overall", "other"]
Frequency = Literal["daily", "weekly", "monthly", "rarely", "unclear"]
WorryKind = Literal["losing_money", "where_is_my_money", "how_sip_works", "charges_or_tax", "app_status_or_error",
                    "whether_to_continue", "other"]
Channel = Literal["youtube_creator", "friends_family", "advisor_agent_bank", "search_web", "social_or_forum",
                  "customer_support", "other"]


class Check(BaseModel):
    what: CheckWhat
    frequency: Frequency = "unclear"
    evidence_span: str = Field(min_length=1)


class Worry(BaseModel):
    kind: WorryKind
    evidence_span: str = Field(min_length=1)


class OutsideHelp(BaseModel):
    channel: Channel
    evidence_span: str = Field(min_length=1)


class Signal(BaseModel):
    value: str
    evidence_span: str | None = None   # required unless value is "unclear"


class Segment(BaseModel):
    age_band: Signal = Signal(value="unclear")          # <25 | 25-34 | 35-44 | 45+ | unclear
    income_stability: Signal = Signal(value="unclear")  # salaried | irregular_or_business | student_no_income | retired | homemaker | unclear
    money_source: Signal = Signal(value="unclear")      # salary_savings | lumpsum_or_windfall | family_money | unclear
    influencer: Signal = Signal(value="unclear")        # self | youtube_creator | friends_family | advisor_agent_bank | ads_or_app | unclear

    @field_validator("age_band", "income_stability", "money_source", "influencer")
    @classmethod
    def allowed(cls, v: Signal, info: ValidationInfo) -> Signal:
        ok = {"age_band": {"<25", "25-34", "35-44", "45+"},
              "income_stability": {"salaried", "irregular_or_business", "student_no_income", "retired", "homemaker"},
              "money_source": {"salary_savings", "lumpsum_or_windfall", "family_money"},
              "influencer": {"self", "youtube_creator", "friends_family", "advisor_agent_bank", "ads_or_app"}}[info.field_name]
        if v.value != "unclear" and v.value not in ok:
            raise ValueError(f"{info.field_name}: {v.value!r} not allowed")
        return v


class ContextExtraction(BaseModel):
    record_id: str
    checks: list[Check] = []          # what they check after starting, and how often
    worries: list[Worry] = []         # what confuses or worries them inside the app
    outside_help: list[OutsideHelp] = []  # what they do / who they turn to outside the app when unsure
    segment: Segment = Segment()
