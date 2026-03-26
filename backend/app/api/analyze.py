from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.models import (
    AnalysisMetadata,
    AnalysisRequest,
    AnalysisResponse,
    CostFraming,
    DevelopmentEnvelope,
    ParcelInfo,
    ProcessTimeline,
    RiskMap,
    Scenario,
    Setbacks,
)

router = APIRouter()

JURISDICTION_DISPLAY = {
    "charleston": "City of Charleston",
    "mount_pleasant": "Town of Mount Pleasant",
    "north_charleston": "City of North Charleston",
    "sullivans_island": "Town of Sullivan's Island",
    "isle_of_palms": "City of Isle of Palms",
    "folly_beach": "City of Folly Beach",
    "james_island": "James Island (Unincorporated)",
    "kiawah": "Town of Kiawah Island",
    "summerville": "Town of Summerville",
    "goose_creek": "City of Goose Creek",
    "hanahan": "City of Hanahan",
    "unincorporated": "Charleston County (Unincorporated)",
}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_parcel(request: AnalysisRequest):
    jurisdiction_display = JURISDICTION_DISPLAY.get(
        request.jurisdiction.value, request.jurisdiction.value
    )

    return AnalysisResponse(
        parcel=ParcelInfo(
            address=request.address,
            jurisdiction=request.jurisdiction.value,
            jurisdiction_display=jurisdiction_display,
            zoning_district="SR-2",
            lot_size_sf=request.lot_size_sf or 7500.0,
        ),
        envelope=DevelopmentEnvelope(
            zoning_district="SR-2",
            zoning_description="Single-Family Residential — moderate density",
            permitted_uses=["Single-family detached", "Accessory dwelling unit", "Home occupation"],
            conditional_uses=["Duplex", "Bed and breakfast", "Group home"],
            max_height_ft=45.0,
            max_stories=3,
            far=0.75,
            max_lot_coverage_pct=50.0,
            density_units_per_acre=8.0,
            setbacks=Setbacks(front=25.0, side=5.0, rear=20.0),
            buildable_area_sf=3750.0,
            parking_requirements="2 spaces per dwelling unit",
        ),
        scenarios=[
            Scenario(
                name="By-Right",
                unit_count_range="1 unit",
                description="Single-family home built within all current zoning parameters. No variances or special approvals needed.",
                constraints=["45 ft height limit", "50% lot coverage", "Standard setbacks apply"],
                risk_level="Low",
                estimated_timeline="3-4 months to permit",
                board_engagement="Staff-level review only",
            ),
            Scenario(
                name="Optimized",
                unit_count_range="1 unit + ADU",
                description="Primary residence with accessory dwelling unit. Maximizes density within SR-2 allowances.",
                constraints=["ADU must be ≤800 SF", "Owner occupancy required", "One additional parking space"],
                risk_level="Moderate",
                estimated_timeline="4-6 months to permit",
                board_engagement="Staff review with possible Design Review Board",
            ),
            Scenario(
                name="With Variance",
                unit_count_range="2 units",
                description="Duplex conversion requiring conditional use approval from BZA.",
                constraints=["BZA conditional use hearing required", "Neighborhood notification", "Increased parking"],
                risk_level="High",
                estimated_timeline="6-10 months to permit",
                board_engagement="BZA hearing required; potential Planning Commission review",
            ),
        ],
        risk_map=RiskMap(
            historic_overlay="Not in historic district",
            flood_zone="Zone X — minimal flood risk",
            building_category=None,
            accommodation_overlay="Not in accommodation overlay",
            community_sensitivity="Low — established residential area",
            recent_board_decisions="No recent denials in this zone",
            environmental_constraints="Standard tree protection ordinance applies",
        ),
        process_timeline=ProcessTimeline(
            required_boards=["Zoning Staff", "Building Permits"],
            review_sequence="Zoning verification → Building permit application → Plan review → Permit issuance",
            estimated_meetings="1-2 staff reviews",
            estimated_months="3-4",
            current_backlog="Moderate — approximately 4-week review cycle",
            additional_permits=["Stormwater permit", "Tree removal permit (if applicable)"],
        ),
        cost_framing=CostFraming(
            permit_fees_estimate="$3,500 - $5,000",
            construction_cost_range="$225,000 - $375,000",
            tax_credit_eligibility="None identified",
            bailey_bill_eligible=False,
            total_cost_range="$228,500 - $380,000",
        ),
        metadata=AnalysisMetadata(
            generated_at=datetime.now(timezone.utc),
            solver_version="0.1.0-mock",
            ai_model="claude-sonnet-4-20250514",
            jurisdiction_module_version="charleston-0.1.0",
        ),
    )
