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
    case "Low": return { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-400" };
    case "Moderate": return { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-400" };
    case "High": return { bg: "bg-red-100", text: "text-red-700", border: "border-red-400" };
  }
}

function scenarioBorder(name: string) {
  if (name === "By-Right") return "border-l-emerald-500";
  if (name === "Optimized") return "border-l-accent";
  return "border-l-orange-400";
}

/* --- Confidence Badge --- */

function ConfidenceBadge({ tier, label }: { tier: number; label: string }) {
  if (tier === 1) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700 text-sm font-medium">
        <span>&#x2713;</span> {label} &mdash; Calculations from validated zoning ordinance
      </div>
    );
  }
  if (tier === 2) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
        <span>&#x25D0;</span> {label} &mdash; AI analysis using verified regulatory research
      </div>
    );
  }
  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 text-amber-700 text-sm font-medium">
      <span>&#x26A0;</span> {label} &mdash; Verify all figures with local planning department
    </div>
  );
}

/* --- Disclaimer Callout --- */

function DisclaimerCallout({ disclaimer }: { disclaimer: string }) {
  return (
    <div
      className="rounded-lg border-l-4 border-amber-400 px-5 py-4 text-sm text-amber-900 leading-relaxed"
      style={{ backgroundColor: "#FFF8E1" }}
    >
      {disclaimer}
    </div>
  );
}

/* --- Section wrapper --- */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-navy px-6 py-3">
        <h2 className="text-white font-semibold text-base">{title}</h2>
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
    { label: "Buildable Area", value: envelope.buildable_area_sf ? `${fmt(envelope.buildable_area_sf)} SF` : "Provide lot size for calculation" },
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

  // Show asymmetric side setbacks if available
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
          <span className="inline-flex items-center px-3 py-1 rounded-full bg-accent/10 text-accent font-semibold text-sm">
            {envelope.zoning_district}
          </span>
          <span className="text-navy/60 text-sm">{envelope.zoning_description}</span>
        </div>
        <p className="text-sm text-navy/50">
          {parcel.address} &middot; {parcel.jurisdiction_display}
          {parcel.lot_size_sf ? ` \u00b7 ${fmt(parcel.lot_size_sf)} SF` : ""}
        </p>

        {/* Metrics grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {metrics.map((m) => (
            <div key={m.label} className="bg-[#F7FAFC] rounded-lg p-3">
              <div className="text-xs text-navy/50 mb-1">{m.label}</div>
              <div className="text-navy font-semibold text-sm">{m.value}</div>
            </div>
          ))}
        </div>

        {/* Setback notes */}
        {envelope.setbacks.setback_notes && (
          <p className="text-xs text-navy/50 italic">{envelope.setbacks.setback_notes}</p>
        )}

        {/* Permitted uses */}
        <div>
          <div className="text-xs text-navy/50 mb-2">Permitted Uses</div>
          <div className="flex flex-wrap gap-1.5">
            {envelope.permitted_uses.map((u) => (
              <span key={u} className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium">
                {u}
              </span>
            ))}
          </div>
        </div>

        {envelope.conditional_uses.length > 0 && (
          <div>
            <div className="text-xs text-navy/50 mb-2">Conditional Uses</div>
            <div className="flex flex-wrap gap-1.5">
              {envelope.conditional_uses.map((u) => (
                <span key={u} className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium">
                  {u}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Parking */}
        {envelope.parking_requirements && (
          <p className="text-sm text-navy/60">
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
      <h2 className="text-lg font-semibold text-navy px-1">Development Scenarios</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.scenarios.map((s) => {
          const risk = riskColor(s.risk_level);
          return (
            <div
              key={s.name}
              className={`bg-white rounded-xl shadow-sm border border-gray-200 border-l-4 ${scenarioBorder(s.name)} p-5 flex flex-col`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-navy">{s.name}</h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text}`}>
                  {s.risk_level}
                </span>
              </div>

              {s.unit_count_range && (
                <div className="text-accent font-semibold text-sm mb-2">{s.unit_count_range}</div>
              )}

              <p className="text-sm text-navy/70 mb-4 leading-relaxed">{s.description}</p>

              <div className="space-y-3 mt-auto">
                <div>
                  <div className="text-xs text-navy/50 mb-1">Constraints</div>
                  <ul className="space-y-1">
                    {s.constraints.map((c, i) => (
                      <li key={i} className="text-xs text-navy/60 flex items-start gap-1.5">
                        <span className="text-navy/30 mt-0.5">&#x2022;</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-3 border-t border-gray-100 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-navy/50">Timeline</span>
                    <span className="text-navy font-medium">{s.estimated_timeline}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-navy/50">Boards</span>
                    <span className="text-navy font-medium text-right max-w-[60%]">{s.board_engagement}</span>
                  </div>
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

const RISK_FACTORS: { key: keyof AnalysisResponse["risk_map"]; label: string; icon: string }[] = [
  { key: "historic_overlay", label: "Historic Overlay", icon: "\uD83C\uDFDB" },
  { key: "flood_zone", label: "Flood Zone", icon: "\uD83C\uDF0A" },
  { key: "building_category", label: "Building Category", icon: "\uD83C\uDFD7" },
  { key: "accommodation_overlay", label: "Accommodation Overlay", icon: "\uD83C\uDFE8" },
  { key: "community_sensitivity", label: "Community Sensitivity", icon: "\uD83D\uDC65" },
  { key: "recent_board_decisions", label: "Recent Board Decisions", icon: "\u2696\uFE0F" },
  { key: "environmental_constraints", label: "Environmental Constraints", icon: "\uD83C\uDF33" },
];

function RiskMapSection({ data }: AnalysisResultsProps) {
  return (
    <Section title="Risk Map">
      <div className="divide-y divide-gray-100">
        {RISK_FACTORS.map((rf) => {
          const value = data.risk_map[rf.key];
          return (
            <div key={rf.key} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <span className="text-lg leading-none mt-0.5" role="img" aria-label={rf.label}>
                {rf.icon}
              </span>
              <div className="min-w-0">
                <div className="text-sm font-medium text-navy">{rf.label}</div>
                <div className="text-sm text-navy/60">{value || "Not applicable"}</div>
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
  return (
    <Section title="Process & Timeline">
      <div className="space-y-5">
        {/* Duration callout */}
        <div className="bg-accent/5 rounded-lg p-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-navy">Estimated Duration</div>
            <div className="text-xs text-navy/50">{tl.estimated_meetings} meetings</div>
          </div>
          <div className="text-2xl font-bold text-accent">{tl.estimated_months} mo</div>
        </div>

        {/* Backlog warning */}
        {tl.current_backlog && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
            <span className="font-medium">Current backlog:</span> {tl.current_backlog}
          </div>
        )}

        {/* Review sequence steps */}
        <div>
          <div className="text-xs text-navy/50 mb-3">Review Sequence</div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-navy/70">
            {tl.review_sequence.split("\u2192").map((step, i, arr) => (
              <span key={i} className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-accent/10 text-accent text-xs font-semibold flex items-center justify-center">
                    {i + 1}
                  </span>
                  {step.trim()}
                </span>
                {i < arr.length - 1 && (
                  <svg className="w-4 h-4 text-navy/30 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </span>
            ))}
          </div>
        </div>

        {/* Required boards */}
        <div>
          <div className="text-xs text-navy/50 mb-2">Required Boards</div>
          <div className="flex flex-wrap gap-1.5">
            {tl.required_boards.map((b) => (
              <span key={b} className="px-2.5 py-1 rounded-full bg-[#F7FAFC] text-navy text-xs font-medium border border-gray-200">
                {b}
              </span>
            ))}
          </div>
        </div>

        {/* Additional permits */}
        {tl.additional_permits.length > 0 && (
          <div>
            <div className="text-xs text-navy/50 mb-2">Additional Permits</div>
            <ul className="space-y-1">
              {tl.additional_permits.map((p, i) => (
                <li key={i} className="text-sm text-navy/60 flex items-start gap-1.5">
                  <span className="text-navy/30 mt-0.5">&#x2022;</span>
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

  // Add new cost engine fields if present
  if (cf.construction_type) rows.unshift({ label: "Construction Type", value: cf.construction_type });
  if (cf.base_hard_cost_range) rows.push({ label: "Base Hard Cost", value: cf.base_hard_cost_range });
  if (cf.premium_adjusted_range) rows.push({ label: "Premium-Adjusted", value: cf.premium_adjusted_range });
  if (cf.all_in_estimate_range) rows.push({ label: "All-In Estimate", value: cf.all_in_estimate_range });
  if (cf.impact_fees_estimate) rows.push({ label: "Impact Fees", value: cf.impact_fees_estimate });

  return (
    <Section title="Cost Framing (Estimates)">
      <div className="space-y-4">
        <p className="text-xs text-navy/40 italic">
          These are rough estimates for initial feasibility assessment. Not a substitute for professional cost analysis.
        </p>

        {/* Applicable premiums */}
        {cf.applicable_premiums && cf.applicable_premiums.length > 0 && (
          <div>
            <div className="text-xs text-navy/50 mb-2">Applicable Premiums</div>
            <div className="flex flex-wrap gap-1.5">
              {cf.applicable_premiums.map((p) => (
                <span key={p} className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium">
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="divide-y divide-gray-100">
          {rows.map((r) => (
            <div key={r.label} className="flex justify-between py-2.5 first:pt-0">
              <span className="text-sm text-navy/60">{r.label}</span>
              <span className="text-sm text-navy font-medium">{r.value || "\u2014"}</span>
            </div>
          ))}
        </div>

        {cf.total_cost_range && (
          <div className="bg-[#F7FAFC] rounded-lg p-4 flex justify-between items-center">
            <span className="text-sm font-medium text-navy">Total Estimated Range</span>
            <span className="text-lg font-bold text-navy">{cf.total_cost_range}</span>
          </div>
        )}

        {/* CWS fee warning */}
        {cf.cws_fee_warning && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-xs text-amber-800">
            {cf.cws_fee_warning}
          </div>
        )}
      </div>
    </Section>
  );
}

/* --- Footer --- */

function ReportFooter({ data }: AnalysisResultsProps) {
  const ts = new Date(data.metadata.generated_at).toLocaleString();
  return (
    <div className="space-y-4">
      {/* CTAs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <a
          href="https://georgest.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="block bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:border-accent/40 transition-colors"
        >
          <div className="text-sm font-medium text-navy">Ready to submit plans?</div>
          <div className="text-sm text-accent mt-1">Run a Pre-Flight on GeorgeSt.ai &rarr;</div>
        </a>
        <a
          href="mailto:only@halfdays.ai"
          className="block bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:border-accent/40 transition-colors"
        >
          <div className="text-sm font-medium text-navy">Need help navigating this?</div>
          <div className="text-sm text-accent mt-1">Talk to Halfdays &rarr;</div>
        </a>
      </div>

      {/* Meta */}
      <div className="text-center space-y-1 pt-2">
        <p className="text-xs text-navy/30">
          Generated {ts} &middot; Solver {data.metadata.solver_version} &middot; {data.metadata.ai_model}
        </p>
        <p className="text-xs text-navy/40 font-medium">Powered by Halfdays AI</p>
      </div>
    </div>
  );
}

/* --- Main component --- */

export default function AnalysisResults({ data }: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      {/* Confidence badge — always shown */}
      <div className="flex justify-center">
        <ConfidenceBadge tier={data.confidence_tier} label={data.confidence_label} />
      </div>

      {/* Disclaimer callout — Tier 2 and 3 */}
      {data.disclaimer && <DisclaimerCallout disclaimer={data.disclaimer} />}

      <EnvelopeSection data={data} />
      <ScenariosSection data={data} />
      <RiskMapSection data={data} />
      <ProcessSection data={data} />
      <CostSection data={data} />
      <ReportFooter data={data} />
    </div>
  );
}
