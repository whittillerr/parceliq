"""Jurisdiction context formatter for Claude prompt injection.

Transforms a ``JurisdictionModule`` into a structured text block that gives
Claude the regulatory context it needs for analysis.
"""

from __future__ import annotations

from app.jurisdictions.base import JurisdictionModule


def _format_review_boards(boards: list[dict]) -> str:
    if not boards:
        return "No review board data available."
    lines = []
    for b in boards:
        name = b.get("name", "Unknown")
        schedule = b.get("schedule", "")
        backlog = b.get("backlog", "")
        parts = [f"- {name}"]
        if schedule:
            parts.append(f"  Schedule: {schedule}")
        if backlog:
            parts.append(f"  Backlog: {backlog}")
        lines.append("\n".join(parts))
    return "\n".join(lines)


def _format_fee_schedule(fees: dict) -> str:
    if not fees:
        return "No fee schedule data available."
    lines = []
    for key, val in fees.items():
        label = key.replace("_", " ").title()
        lines.append(f"- {label}: {val}")
    return "\n".join(lines)


def _format_overlays(overlays: dict) -> str:
    if not overlays:
        return "No overlay data available."
    lines = []
    for key, val in overlays.items():
        if isinstance(val, dict):
            label = val.get("name", key)
            desc = val.get("description", "")
            lines.append(f"- {label}: {desc}")
        else:
            lines.append(f"- {key}: {val}")
    return "\n".join(lines)


def _format_districts(module: JurisdictionModule) -> str:
    districts = module.list_districts()
    if not districts:
        return "No structured district data available."
    lines = []
    for code in districts:
        data = module.get_district(code)
        if data:
            desc = data.get("description", data.get("zoning_description", ""))
            lines.append(f"- {code}: {desc}" if desc else f"- {code}")
    return "\n".join(lines) if lines else "No structured district data available."


def build_jurisdiction_context(module: JurisdictionModule) -> str:
    """Format a jurisdiction module's data into a structured context block.

    For solver-enabled (Tier 1) jurisdictions, this provides overlay data,
    review boards, and fee schedules alongside the module's own AI context.

    For Tier 2/3 jurisdictions, the module's ``get_ai_context()`` already
    contains the full research dump — we wrap it with structure.
    """
    sections: list[str] = []

    header = f"=== JURISDICTION CONTEXT: {module.name} ==="
    sections.append(header)

    # Regulatory framework summary
    framework_lines = [
        "REGULATORY FRAMEWORK:",
        f"- Bulk control: {module.bulk_control_type}",
        f"- Height unit: {module.height_unit}",
        f"- Solver enabled: {module.solver_enabled}",
        f"- Confidence tier: {module.tier} ({module.confidence_label})",
    ]
    if module.has_height_district_overlays:
        framework_lines.append("- Height district overlays: YES (may override base zoning)")
    sections.append("\n".join(framework_lines))

    # Tier 1: structured data sections
    if module.tier == 1:
        districts_text = _format_districts(module)
        sections.append(f"AVAILABLE DISTRICTS:\n{districts_text}")

        overlays = module.get_overlay_data()
        if overlays:
            sections.append(f"OVERLAY DATA:\n{_format_overlays(overlays)}")

    # Review boards (all tiers that have them)
    boards = module.get_review_boards()
    if boards:
        sections.append(f"REVIEW BOARDS:\n{_format_review_boards(boards)}")

    # Fee schedule
    fees = module.get_fee_schedule()
    if fees:
        sections.append(f"FEE SCHEDULE:\n{_format_fee_schedule(fees)}")

    # Tax credits (applies to all jurisdictions in Charleston County)
    tax_credits = (
        "TAX CREDITS & INCENTIVES:\n"
        "- Federal 20% Historic Tax Credit: applies to QREs on certified "
        "historic structures (income-producing only)\n"
        "- SC does NOT currently offer a state HTC\n"
        "- Bailey Bill: Special assessment for historic rehabilitation — "
        "freezes property tax assessment for up to 20 years\n"
        "- 20% federal HTC is taken ratably over 5 years (post-TCJA)"
    )
    sections.append(tax_credits)

    # AI context from module (the big research text for Tier 2, or summary for Tier 1)
    ai_context = module.get_ai_context()
    if ai_context:
        if module.tier >= 2:
            sections.append(
                f"DIMENSIONAL STANDARDS DATA (from research audit):\n{ai_context}"
            )
        else:
            sections.append(f"ADDITIONAL ZONING CONTEXT:\n{ai_context}")

    sections.append("===")

    return "\n\n".join(sections)
