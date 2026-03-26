from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolverInput:
    jurisdiction: str
    zoning_district: str
    lot_size_sf: Optional[float] = None
    lot_width_ft: Optional[float] = None
    lot_depth_ft: Optional[float] = None
    use_type: str = "residential"
    use_subtype: Optional[str] = None
    height_district: Optional[str] = None
    on_peninsula: Optional[bool] = None
    flood_zone: Optional[str] = None
    historic_overlay: Optional[str] = None
    half_row_width_ft: Optional[float] = None  # for footnote 8; default 25 if None


@dataclass
class SetbackSet:
    front_rear_total: Optional[float] = None
    front: Optional[float] = None
    rear: Optional[float] = None
    side_total: Optional[float] = None
    side_sw: Optional[float] = None
    side_ne: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class DevelopmentEnvelope:
    zoning_district: str = ""
    zoning_description: str = ""
    max_height_ft: Optional[float] = None
    max_height_stories: Optional[float] = None
    effective_height_ft: Optional[float] = None
    effective_height_stories: Optional[float] = None
    height_controlling_factor: Optional[str] = None
    lot_occupancy_pct: Optional[float] = None
    far: Optional[float] = None
    density_units_per_acre: Optional[float] = None
    density_basis: Optional[str] = None
    setbacks: SetbackSet = field(default_factory=SetbackSet)
    max_building_footprint_sf: Optional[float] = None
    max_gross_floor_area_sf: Optional[float] = None
    max_units: Optional[int] = None
    parking_required: Optional[float] = None
    parking_type: Optional[str] = None
    height_district_required: bool = False


@dataclass
class ScenarioOutput:
    name: str = ""
    risk_level: str = "Low"
    unit_count_low: Optional[int] = None
    unit_count_high: Optional[int] = None
    gross_floor_area_sf: Optional[float] = None
    stories: Optional[float] = None
    description: str = ""
    constraints_satisfied: List[str] = field(default_factory=list)
    constraints_exceeded: List[str] = field(default_factory=list)
    variance_needed: List[str] = field(default_factory=list)


@dataclass
class BindingConstraint:
    constraint_name: str = ""
    constraint_value: str = ""
    is_binding: bool = False
    explanation: str = ""


@dataclass
class SolverOutput:
    envelope: DevelopmentEnvelope = field(default_factory=DevelopmentEnvelope)
    scenarios: List[ScenarioOutput] = field(default_factory=list)
    binding_constraints: List[BindingConstraint] = field(default_factory=list)
    solver_mode: str = "full"  # "full", "partial", "ai_only"
    jurisdiction_engine: str = ""
    warnings: List[str] = field(default_factory=list)
    confidence: str = "high"  # "high", "moderate", "low"
    ai_context: Optional[str] = None
