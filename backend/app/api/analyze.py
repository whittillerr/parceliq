from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Optional

router = APIRouter()


class AnalyzeRequest(BaseModel):
    parcel_id: Optional[str] = None
    address: Optional[str] = None
    params: dict[str, Any] = {}


class AnalyzeResponse(BaseModel):
    parcel_id: str
    feasibility: str
    zoning: str
    max_units: int
    risks: list[str]
    summary: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_parcel(request: AnalyzeRequest):
    return AnalyzeResponse(
        parcel_id=request.parcel_id or "TMS-000-00-00-000",
        feasibility="favorable",
        zoning="SR-1 (Single-Family Residential)",
        max_units=1,
        risks=["Flood zone AE — requires elevation certificate", "Tree ordinance buffer may reduce buildable area"],
        summary="Mock analysis: This parcel appears suitable for single-family residential development pending flood zone and tree survey review.",
    )
