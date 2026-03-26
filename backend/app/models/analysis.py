from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# --- Enums ---

class Jurisdiction(str, Enum):
    CHARLESTON = "charleston"
    MOUNT_PLEASANT = "mount_pleasant"
    NORTH_CHARLESTON = "north_charleston"
    SULLIVANS_ISLAND = "sullivans_island"
    ISLE_OF_PALMS = "isle_of_palms"
    FOLLY_BEACH = "folly_beach"
    JAMES_ISLAND = "james_island"
    KIAWAH = "kiawah"
    SUMMERVILLE = "summerville"
    GOOSE_CREEK = "goose_creek"
    HANAHAN = "hanahan"
    UNINCORPORATED = "unincorporated"


class UseType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    HOSPITALITY = "hospitality"
    ADAPTIVE_REUSE = "adaptive_reuse"


class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


# --- Request ---

class AnalysisRequest(BaseModel):
    jurisdiction: Jurisdiction
    address: str
    zoning_district: Optional[str] = None
    height_district: Optional[str] = None
    on_peninsula: Optional[bool] = None
    flood_zone: Optional[str] = None
    historic_overlay: Optional[str] = None
    lot_size_sf: Optional[float] = None
    use_types: Optional[List[UseType]] = None
    approximate_scale: Optional[str] = None
    existing_conditions: Optional[str] = None
    additional_context: Optional[str] = None


# --- Response sub-models ---

class ParcelInfo(BaseModel):
    address: str
    jurisdiction: str
    jurisdiction_display: str
    zoning_district: Optional[str] = None
    lot_size_sf: Optional[float] = None


class Setbacks(BaseModel):
    front: Optional[float] = None
    side: Optional[float] = None
    rear: Optional[float] = None
    front_rear_total: Optional[float] = None
    side_sw: Optional[float] = None
    side_ne: Optional[float] = None
    setback_notes: Optional[str] = None


class DevelopmentEnvelope(BaseModel):
    zoning_district: str
    zoning_description: str
    permitted_uses: List[str]
    conditional_uses: List[str]
    max_height_ft: Optional[float] = None
    max_stories: Optional[int] = None
    far: Optional[float] = None
    max_lot_coverage_pct: Optional[float] = None
    density_units_per_acre: Optional[float] = None
    setbacks: Setbacks
    buildable_area_sf: Optional[float] = None
    parking_requirements: Optional[str] = None
    lot_occupancy_pct: Optional[float] = None
    height_source: Optional[str] = None
    binding_constraint: Optional[str] = None


class Scenario(BaseModel):
    name: str
    unit_count_range: Optional[str] = None
    description: str
    constraints: List[str]
    risk_level: RiskLevel
    estimated_timeline: str
    board_engagement: str


class RiskMap(BaseModel):
    historic_overlay: Optional[str] = None
    flood_zone: Optional[str] = None
    building_category: Optional[str] = None
    accommodation_overlay: Optional[str] = None
    community_sensitivity: Optional[str] = None
    recent_board_decisions: Optional[str] = None
    environmental_constraints: Optional[str] = None


class ProcessTimeline(BaseModel):
    required_boards: List[str]
    review_sequence: str
    estimated_meetings: str
    estimated_months: str
    current_backlog: Optional[str] = None
    additional_permits: List[str]


class CostFraming(BaseModel):
    permit_fees_estimate: Optional[str] = None
    construction_cost_range: Optional[str] = None
    tax_credit_eligibility: Optional[str] = None
    bailey_bill_eligible: Optional[bool] = None
    total_cost_range: Optional[str] = None
    construction_type: Optional[str] = None
    base_hard_cost_range: Optional[str] = None
    applicable_premiums: Optional[List[str]] = None
    premium_adjusted_range: Optional[str] = None
    all_in_estimate_range: Optional[str] = None
    impact_fees_estimate: Optional[str] = None
    cws_fee_warning: Optional[str] = None


class ScenarioCommentary(BaseModel):
    by_right: str = ""
    optimized: str = ""
    with_variance: str = ""


class AnalysisMetadata(BaseModel):
    generated_at: datetime
    solver_version: str
    ai_model: str
    jurisdiction_module_version: str


# --- Response ---

class AnalysisResponse(BaseModel):
    parcel: ParcelInfo
    envelope: DevelopmentEnvelope
    scenarios: List[Scenario] = Field(..., min_length=3, max_length=3)
    risk_map: RiskMap
    process_timeline: ProcessTimeline
    cost_framing: CostFraming
    metadata: AnalysisMetadata
    confidence_tier: int
    confidence_label: str
    disclaimer: Optional[str] = None
