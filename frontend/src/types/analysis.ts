// --- Enums ---

export type Jurisdiction =
  | "charleston"
  | "mount_pleasant"
  | "north_charleston"
  | "sullivans_island"
  | "isle_of_palms"
  | "folly_beach"
  | "james_island"
  | "kiawah"
  | "summerville"
  | "goose_creek"
  | "hanahan"
  | "unincorporated";

export type UseType =
  | "residential"
  | "commercial"
  | "mixed_use"
  | "hospitality"
  | "adaptive_reuse";

export type RiskLevel = "Low" | "Moderate" | "High";

// --- Request ---

export interface AnalysisRequest {
  jurisdiction: Jurisdiction;
  address: string;
  lot_size_sf?: number;
  use_types?: UseType[];
  approximate_scale?: string;
  existing_conditions?: string;
  additional_context?: string;
}

// --- Response sub-models ---

export interface ParcelInfo {
  address: string;
  jurisdiction: string;
  jurisdiction_display: string;
  zoning_district?: string;
  lot_size_sf?: number;
}

export interface Setbacks {
  front?: number;
  side?: number;
  rear?: number;
  front_rear_total?: number;
  side_sw?: number;
  side_ne?: number;
  setback_notes?: string;
}

export interface DevelopmentEnvelope {
  zoning_district: string;
  zoning_description: string;
  permitted_uses: string[];
  conditional_uses: string[];
  max_height_ft?: number;
  max_stories?: number;
  far?: number;
  max_lot_coverage_pct?: number;
  density_units_per_acre?: number;
  setbacks: Setbacks;
  buildable_area_sf?: number;
  parking_requirements?: string;
  lot_occupancy_pct?: number;
  height_source?: string;
  binding_constraint?: string;
}

export interface Scenario {
  name: string;
  unit_count_range?: string;
  description: string;
  constraints: string[];
  risk_level: RiskLevel;
  estimated_timeline: string;
  board_engagement: string;
}

export interface RiskMap {
  historic_overlay?: string;
  flood_zone?: string;
  building_category?: string;
  accommodation_overlay?: string;
  community_sensitivity?: string;
  recent_board_decisions?: string;
  environmental_constraints?: string;
}

export interface ProcessTimeline {
  required_boards: string[];
  review_sequence: string;
  estimated_meetings: string;
  estimated_months: string;
  current_backlog?: string;
  additional_permits: string[];
}

export interface CostFraming {
  permit_fees_estimate?: string;
  construction_cost_range?: string;
  tax_credit_eligibility?: string;
  bailey_bill_eligible?: boolean;
  total_cost_range?: string;
  construction_type?: string;
  base_hard_cost_range?: string;
  applicable_premiums?: string[];
  premium_adjusted_range?: string;
  all_in_estimate_range?: string;
  impact_fees_estimate?: string;
  cws_fee_warning?: string;
}

export interface AnalysisMetadata {
  generated_at: string;
  solver_version: string;
  ai_model: string;
  jurisdiction_module_version: string;
}

// --- Response ---

export interface AnalysisResponse {
  parcel: ParcelInfo;
  envelope: DevelopmentEnvelope;
  scenarios: [Scenario, Scenario, Scenario];
  risk_map: RiskMap;
  process_timeline: ProcessTimeline;
  cost_framing: CostFraming;
  metadata: AnalysisMetadata;
  confidence_tier: number; // 1, 2, or 3
  confidence_label: string;
  disclaimer?: string;
}
