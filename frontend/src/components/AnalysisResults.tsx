import type { AnalysisResponse, RiskLevel } from "../types/analysis";

interface AnalysisResultsProps {
  data: AnalysisResponse;
}

/* --- Helpers --- */

function fmt(val: number | undefined | null, suffix = ""): string {
  if (val == null) return "\u2014";
  return val.toLocaleString() + suffix;
}

function riskColor(level: RiskLevel) {
  switch (level) {
    case "Low": return { bg: "bg-emerald-50", text: "text-success", dot: "bg-success" };
    case "Moderate": return { bg: "bg-amber-50", text: "text-warning", dot: "bg-warning" };
    case "High": return { bg: "bg-red-50", text: "text-danger", dot: "bg-danger" };
  }
}

function scenarioBorder(name: string) {
  if (name === "By-Right") return "border-l-success";
  if (name === "Optimized") return "border-l-accent";
  return "border-l-warning";
}

/* --- Confidence Badge --- */

function ConfidenceBadge({ tier, label }: { tier: number; label: string }) {
  const styles = {
    1: { bg: "bg-emerald-50", text: "text-success", border: "border-success/20" },
    2: { bg: "bg-accent-light", text: "text-accent", border: "border-accent/20" },
    3: { bg: "bg-amber-50", text: "text-warning", border: "border-warning/20" },
  }[tier] ?? { bg: "bg-gray-50", text: "text-muted", border: "border-border" };

  const icons = { 1: "\u2713", 2: "\u25D0", 3: "\u26A0" };
  const descriptions = {
    1: "Calculations from validated zoning ordinance",
    2: "AI analysis using verified regulatory research",
    3: "Verify all figures with local planning department",
  };

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${styles.bg} ${styles.text} border ${styles.border} text-sm font-medium`}>
      <span className="text-base leading-none">{icons[tier as 1 | 2 | 3]}</span>
      <span>{label}</span>
      <span className="hidden sm:inline opacity-60">&mdash; {descriptions[tier as 1 | 2 | 3]}</span>
    </div>
  );
}

/* --- Disclaimer Callout --- */

function DisclaimerCallout({ disclaimer }: { disclaimer: string }) {
  return (
    <div className="rounded-card border-l-4 border-warning bg-amber-50/50 px-5 py-4 text-sm text-navy/70 leading-relaxed">
      {disclaimer}
    </div>
  );
}

/* --- Executive Summary --- */

function ExecutiveSummary({ summary }: { summary: string }) {
  return (
    <div className="bg-white rounded-card shadow-card border border-border border-l-4 border-l-accent overflow-hidden">
      <div className="px-6 py-5">
        <h2 className="text-xs font-semibold text-accent uppercase tracking-wider mb-2">Development Potential</h2>
        <p className="text-sm text-navy leading-relaxed">{summary}</p>
      </div>
    </div>
  );
}

/* --- Section wrapper --- */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-card shadow-card border border-border overflow-hidden">
      <div className="bg-navy px-6 py-3.5">
        <h2 className="text-white font-semibold text-sm tracking-wide">{title}</h2>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

/* --- 1. Development Envelope --- */

function EnvelopeSection({ data }: AnalysisResultsProps) {
  const { envelope, parcel } = data;
  const heightStr = [
    envelope.max_height_ft ? `${envelope.max_height_ft} ft` : null,
    envelope.max_stories ? `${envelope.max_stories} stories` : null,
  ].filter(Boolean).join(" / ") || "\u2014";

  const metrics: { label: string; value: string }[] = [
    { label: "Max Height", value: heightStr },
    { label: "FAR", value: envelope.far != null ? String(envelope.far) : "\u2014" },
    { label: "Lot Coverage", value: envelope.max_lot_coverage_pct != null ? `${envelope.max_lot_coverage_pct}%` : "\u2014" },
    { label: "Density", value: envelope.density_units_per_acre != null ? `${envelope.density_units_per_acre} units/acre` : "\u2014" },
    { label: "Front Setback", value: envelope.setbacks.front != null ? `${envelope.setbacks.front} ft` : "\u2014" },
    { label: "Buildable Area", value: envelope.buildable_area_sf ? `${fmt(envelope.buildable_area_sf)} SF` : "Provide lot size" },
  ];

  if (envelope.lot_occupancy_pct != null) {
    metrics.splice(2, 0, { label: "Lot Occupancy", value: `${envelope.lot_occupancy_pct}%` });
  }
  if (envelope.height_source) {
    metrics.push({ label: "Height Source", value: envelope.height_source });
  }
  if (envelope.binding_constraint) {
    metrics.push({ label: "Binding Constraint", value: envelope.binding_constraint });
  }

  const setbackDetails: string[] = [];
  if (envelope.setbacks.side_sw != null) setbackDetails.push(`SW: ${envelope.setbacks.side_sw} ft`);
  if (envelope.setbacks.side_ne != null) setbackDetails.push(`NE: ${envelope.setbacks.side_ne} ft`);
  if (setbackDetails.length > 0) {
    metrics.push({ label: "Side Setbacks", value: setbackDetails.join(" / ") });
  }

  return (
    <Section title="Development Envelope">
      <div className="space-y-5">
        {/* Zoning badge + parcel */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center px-3 py-1 rounded-full bg-accent-light text-accent font-semibold text-sm">
            {envelope.zoning_district}
          </span>
          <span className="text-muted text-sm">{envelope.zoning_description}</span>
        </div>
        <p className="text-sm text-muted">
          {parcel.address} &middot; {parcel.jurisdiction_display}
          {parcel.lot_size_sf ? ` \u00b7 ${fmt(parcel.lot_size_sf)} SF` : ""}
        </p>

        {/* Metrics grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {metrics.map((m) => (
            <div key={m.label} className="bg-[#F7FAFC] rounded-btn p-3">
              <div className="text-xs text-muted mb-1">{m.label}</div>
              <div className="text-navy font-semibold text-sm">{m.value}</div>
            </div>
          ))}
        </div>

        {/* Setback notes */}
        {envelope.setbacks.setback_notes && (
          <p className="text-xs text-muted italic">{envelope.setbacks.setback_notes}</p>
        )}

        {/* Uses */}
        {envelope.permitted_uses.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-2">Permitted Uses</div>
            <div className="flex flex-wrap gap-1.5">
              {envelope.permitted_uses.map((u) => (
                <span key={u} className="px-2.5 py-1 rounded-full bg-emerald-50 text-success text-xs font-medium">
                  {u}
                </span>
              ))}
            </div>
          </div>
        )}

        {envelope.conditional_uses.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-2">Conditional Uses</div>
            <div className="flex flex-wrap gap-1.5">
              {envelope.conditional_uses.map((u) => (
                <span key={u} className="px-2.5 py-1 rounded-full bg-amber-50 text-warning text-xs font-medium">
                  {u}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Parking */}
        {envelope.parking_requirements && (
          <p className="text-sm text-muted">
            <span className="font-medium text-navy">Parking:</span> {envelope.parking_requirements}
          </p>
        )}
      </div>
    </Section>
  );
}

/* --- 2. Scenarios --- */

function ScenariosSection({ data }: AnalysisResultsProps) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-navy uppercase tracking-wider px-1">Development Scenarios</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.scenarios.map((s) => {
          const risk = riskColor(s.risk_level);
          return (
            <div
              key={s.name}
              className={`bg-white rounded-card shadow-card border border-border border-l-4 ${scenarioBorder(s.name)} p-5 flex flex-col hover:shadow-card-hover transition-shadow`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-navy text-sm">{s.name}</h3>
                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${risk.dot}`} />
                  {s.risk_level}
                </span>
              </div>

              {s.unit_count_range && (
                <div className="text-accent font-bold text-base mb-2">{s.unit_count_range}</div>
              )}

              <p className="text-sm text-muted mb-4 leading-relaxed flex-1">{s.description}</p>

              <div className="space-y-3 mt-auto">
                {s.constraints.length > 0 && (
                  <div>
                    <div className="text-xs text-muted mb-1.5">Constraints</div>
                    <ul className="space-y-1">
                      {s.constraints.map((c, i) => (
                        <li key={i} className="text-xs text-muted flex items-start gap-1.5">
                          <span className="text-navy/20 mt-0.5">&bull;</span>
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-3 border-t border-border space-y-1.5">
                  {s.estimated_timeline && (
                    <div className="flex justify-between text-xs">
                      <span className="text-muted">Timeline</span>
                      <span className="text-navy font-medium">{s.estimated_timeline}</span>
                    </div>
                  )}
                  {s.board_engagement && (
                    <div className="flex justify-between text-xs">
                      <span className="text-muted">Boards</span>
                      <span className="text-navy font-medium text-right max-w-[60%]">{s.board_engagement}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* --- 3. Risk Map --- */

function riskSeverity(value: string | undefined): "low" | "moderate" | "high" | "none" {
  if (!value || value === "Not applicable" || value === "None") return "none";
  const lower = value.toLowerCase();
  if (lower.includes("high") || lower.includes("significant") || lower.includes("critical")) return "high";
  if (lower.includes("moderate") || lower.includes("some") || lower.includes("partial")) return "moderate";
  return "low";
}

const SEVERITY_DOT: Record<string, string> = {
  none: "bg-gray-300",
  low: "bg-success",
  moderate: "bg-warning",
  high: "bg-danger",
};

const RISK_FACTORS: { key: keyof AnalysisResponse["risk_map"]; label: string }[] = [
  { key: "historic_overlay", label: "Historic Overlay" },
  { key: "flood_zone", label: "Flood Zone" },
  { key: "building_category", label: "Building Category" },
  { key: "accommodation_overlay", label: "Accommodation Overlay" },
  { key: "community_sensitivity", label: "Community Sensitivity" },
  { key: "recent_board_decisions", label: "Recent Board Decisions" },
  { key: "environmental_constraints", label: "Environmental Constraints" },
];

function RiskMapSection({ data }: AnalysisResultsProps) {
  return (
    <Section title="Risk Map">
      <div className="divide-y divide-border">
        {RISK_FACTORS.map((rf) => {
          const value = data.risk_map[rf.key];
          const severity = riskSeverity(value);
          return (
            <div key={rf.key} className="flex items-start gap-3 py-3.5 first:pt-0 last:pb-0">
              <span className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${SEVERITY_DOT[severity]}`} />
              <div className="min-w-0">
                <div className="text-sm font-medium text-navy">{rf.label}</div>
                <div className="text-sm text-muted">{value || "Not applicable"}</div>
              </div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

/* --- 4. Process & Timeline --- */

function ProcessSection({ data }: AnalysisResultsProps) {
  const tl = data.process_timeline;
  const steps = tl.review_sequence
    ? tl.review_sequence.split(/\u2192|->|→/).map((s) => s.trim()).filter(Boolean)
    : [];

  return (
    <Section title="Process & Timeline">
      <div className="space-y-5">
        {/* Duration callout */}
        <div className="bg-accent-light rounded-card p-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-navy">Estimated Duration</div>
            <div className="text-xs text-muted">{tl.estimated_meetings} meetings</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-accent leading-none">{tl.estimated_months}</div>
            <div className="text-xs text-muted">months</div>
          </div>
        </div>

        {/* Backlog warning */}
        {tl.current_backlog && (
          <div className="bg-amber-50 border border-warning/20 rounded-btn px-4 py-3 text-sm text-navy/70">
            <span className="font-medium text-warning">Current backlog:</span> {tl.current_backlog}
          </div>
        )}

        {/* Horizontal step diagram */}
        {steps.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-3">Review Sequence</div>
            <div className="flex items-center gap-0 overflow-x-auto pb-2">
              {steps.map((step, i) => (
                <div key={i} className="flex items-center flex-shrink-0">
                  <div className="flex items-center gap-2 bg-[#F7FAFC] border border-border rounded-btn px-3 py-2">
                    <span className="w-5 h-5 rounded-full bg-accent text-white text-xs font-semibold flex items-center justify-center flex-shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-xs text-navy font-medium whitespace-nowrap">{step}</span>
                  </div>
                  {i < steps.length - 1 && (
                    <svg className="w-5 h-5 text-muted/40 flex-shrink-0 mx-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Required boards */}
        {tl.required_boards.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-2">Required Boards</div>
            <div className="flex flex-wrap gap-1.5">
              {tl.required_boards.map((b) => (
                <span key={b} className="px-2.5 py-1 rounded-full bg-[#F7FAFC] text-navy text-xs font-medium border border-border">
                  {b}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Additional permits */}
        {tl.additional_permits.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-2">Additional Permits</div>
            <ul className="space-y-1">
              {tl.additional_permits.map((p, i) => (
                <li key={i} className="text-sm text-muted flex items-start gap-1.5">
                  <span className="text-navy/20 mt-0.5">&bull;</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Section>
  );
}

/* --- 5. Cost Framing --- */

function CostSection({ data }: AnalysisResultsProps) {
  const cf = data.cost_framing;

  const rows: { label: string; value: string | null | undefined }[] = [
    { label: "Permit Fees", value: cf.permit_fees_estimate },
    { label: "Construction Cost", value: cf.construction_cost_range },
    { label: "Tax Credit Eligibility", value: cf.tax_credit_eligibility },
    { label: "Bailey Bill Eligible", value: cf.bailey_bill_eligible != null ? (cf.bailey_bill_eligible ? "Yes" : "No") : null },
  ];

  if (cf.construction_type) rows.unshift({ label: "Construction Type", value: cf.construction_type });
  if (cf.base_hard_cost_range) rows.push({ label: "Base Hard Cost", value: cf.base_hard_cost_range });
  if (cf.premium_adjusted_range) rows.push({ label: "Premium-Adjusted", value: cf.premium_adjusted_range });
  if (cf.all_in_estimate_range) rows.push({ label: "All-In Estimate", value: cf.all_in_estimate_range });
  if (cf.impact_fees_estimate) rows.push({ label: "Impact Fees", value: cf.impact_fees_estimate });

  return (
    <Section title="Cost Framing (Estimates)">
      <div className="space-y-4">
        <p className="text-xs text-muted italic">
          Rough estimates for initial feasibility assessment. Not a substitute for professional cost analysis.
        </p>

        {/* Applicable premiums */}
        {cf.applicable_premiums && cf.applicable_premiums.length > 0 && (
          <div>
            <div className="text-xs text-muted mb-2">Applicable Premiums</div>
            <div className="flex flex-wrap gap-1.5">
              {cf.applicable_premiums.map((p) => (
                <span key={p} className="px-2.5 py-1 rounded-full bg-amber-50 text-warning text-xs font-medium">
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="divide-y divide-border">
          {rows.map((r) => (
            <div key={r.label} className="flex justify-between py-2.5 first:pt-0">
              <span className="text-sm text-muted">{r.label}</span>
              <span className="text-sm text-navy font-medium">{r.value || "\u2014"}</span>
            </div>
          ))}
        </div>

        {cf.total_cost_range && (
          <div className="bg-accent-light rounded-card p-4 flex justify-between items-center">
            <span className="text-sm font-semibold text-navy">Total Estimated Range</span>
            <span className="text-lg font-bold text-accent">{cf.total_cost_range}</span>
          </div>
        )}

        {/* CWS fee warning */}
        {cf.cws_fee_warning && (
          <div className="bg-amber-50 border border-warning/20 rounded-btn px-4 py-3 text-xs text-navy/70">
            {cf.cws_fee_warning}
          </div>
        )}
      </div>
    </Section>
  );
}

/* --- Report Metadata --- */

function ReportMeta({ data }: AnalysisResultsProps) {
  const ts = new Date(data.metadata.generated_at).toLocaleString();
  return (
    <div className="text-center space-y-1 pt-2">
      <p className="text-xs text-muted/50">
        Generated {ts} &middot; Solver {data.metadata.solver_version} &middot; {data.metadata.ai_model}
      </p>
    </div>
  );
}

/* --- Main component --- */

export default function AnalysisResults({ data }: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      {/* Confidence badge */}
      <div className="flex justify-center">
        <ConfidenceBadge tier={data.confidence_tier} label={data.confidence_label} />
      </div>

      {/* Executive Summary */}
      {data.executive_summary && (
        <ExecutiveSummary summary={data.executive_summary} />
      )}

      {/* Disclaimer callout — Tier 2 and 3 */}
      {data.disclaimer && <DisclaimerCallout disclaimer={data.disclaimer} />}

      <EnvelopeSection data={data} />
      <ScenariosSection data={data} />
      <RiskMapSection data={data} />
      <ProcessSection data={data} />
      <CostSection data={data} />
      <ReportMeta data={data} />
    </div>
  );
}
