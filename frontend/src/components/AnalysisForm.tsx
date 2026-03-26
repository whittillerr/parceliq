import { useState } from "react";
import type { AnalysisRequest, AnalysisResponse, Jurisdiction, UseType } from "../types/analysis";
import { analyzeParcel } from "../api/client";

const TIER_1_JURISDICTIONS: { value: Jurisdiction; label: string }[] = [
  { value: "charleston", label: "City of Charleston" },
  { value: "mount_pleasant", label: "Town of Mount Pleasant" },
];

const TIER_2_JURISDICTIONS: { value: Jurisdiction; label: string }[] = [
  { value: "north_charleston", label: "City of North Charleston" },
  { value: "unincorporated", label: "Unincorporated Charleston County" },
];

const TIER_3_JURISDICTIONS: { value: Jurisdiction; label: string }[] = [
  { value: "sullivans_island", label: "Town of Sullivan's Island" },
  { value: "isle_of_palms", label: "City of Isle of Palms" },
  { value: "folly_beach", label: "City of Folly Beach" },
  { value: "james_island", label: "Town of James Island" },
  { value: "kiawah", label: "Town of Kiawah Island" },
  { value: "summerville", label: "Town of Summerville" },
  { value: "goose_creek", label: "City of Goose Creek" },
  { value: "hanahan", label: "City of Hanahan" },
];

const USE_TYPE_OPTIONS: { value: UseType | "unsure"; label: string }[] = [
  { value: "residential", label: "Residential" },
  { value: "commercial", label: "Commercial" },
  { value: "mixed_use", label: "Mixed-Use" },
  { value: "hospitality", label: "Hospitality" },
  { value: "adaptive_reuse", label: "Adaptive Reuse" },
  { value: "unsure", label: "Unsure" },
];

const INPUT_CLASS =
  "w-full h-11 rounded-input border border-border px-4 text-sm text-navy bg-white " +
  "placeholder:text-muted/60 " +
  "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent " +
  "transition-all duration-150";

const LABEL_CLASS = "block text-sm font-medium text-navy mb-1.5";

function parseLotSize(input: string): number | undefined {
  const trimmed = input.trim().toLowerCase();
  if (!trimmed) return undefined;

  const acreMatch = trimmed.match(/^([\d,.]+)\s*(?:acres?|ac)$/);
  if (acreMatch) {
    const acres = parseFloat(acreMatch[1].replace(/,/g, ""));
    return isNaN(acres) ? undefined : Math.round(acres * 43560);
  }

  const sfMatch = trimmed.match(/^([\d,.]+)\s*(?:sf|sq\s*ft|square\s*feet)?$/);
  if (sfMatch) {
    const sf = parseFloat(sfMatch[1].replace(/,/g, ""));
    return isNaN(sf) ? undefined : sf;
  }

  return undefined;
}

function getJurisdictionTier(jurisdiction: Jurisdiction | ""): number | null {
  if (!jurisdiction) return null;
  if (TIER_1_JURISDICTIONS.some((j) => j.value === jurisdiction)) return 1;
  if (TIER_2_JURISDICTIONS.some((j) => j.value === jurisdiction)) return 2;
  if (TIER_3_JURISDICTIONS.some((j) => j.value === jurisdiction)) return 3;
  return null;
}

interface AnalysisFormProps {
  onAnalysisComplete: (response: AnalysisResponse) => void;
  onLoadingChange?: (loading: boolean) => void;
}

export default function AnalysisForm({ onAnalysisComplete, onLoadingChange }: AnalysisFormProps) {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction | "">("");
  const [address, setAddress] = useState("");
  const [lotSizeInput, setLotSizeInput] = useState("");
  const [zoningDistrict, setZoningDistrict] = useState("");
  const [heightDistrict, setHeightDistrict] = useState("");
  const [onPeninsula, setOnPeninsula] = useState(false);
  const [selectedUseTypes, setSelectedUseTypes] = useState<Set<UseType | "unsure">>(new Set());
  const [approximateScale, setApproximateScale] = useState("");
  const [existingConditions, setExistingConditions] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [showOptional, setShowOptional] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tier = getJurisdictionTier(jurisdiction);
  const needsZoning = tier === 1;
  const canSubmit =
    jurisdiction !== "" &&
    address.trim() !== "" &&
    (!needsZoning || zoningDistrict.trim() !== "") &&
    !loading;

  function toggleUseType(value: UseType | "unsure") {
    setSelectedUseTypes((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    onLoadingChange?.(true);
    setError(null);

    const useTypes = [...selectedUseTypes].filter((v): v is UseType => v !== "unsure");

    const request: AnalysisRequest = {
      jurisdiction: jurisdiction as Jurisdiction,
      address: address.trim(),
      ...(zoningDistrict.trim() && { zoning_district: zoningDistrict.trim() }),
      ...(heightDistrict.trim() && { height_district: heightDistrict.trim() }),
      ...(jurisdiction === "charleston" && { on_peninsula: onPeninsula }),
      ...(lotSizeInput && { lot_size_sf: parseLotSize(lotSizeInput) }),
      ...(useTypes.length > 0 && { use_types: useTypes }),
      ...(approximateScale.trim() && { approximate_scale: approximateScale.trim() }),
      ...(existingConditions.trim() && { existing_conditions: existingConditions.trim() }),
      ...(additionalContext.trim() && { additional_context: additionalContext.trim() }),
    };

    try {
      const response = await analyzeParcel(request);
      onAnalysisComplete(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
      onLoadingChange?.(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-card shadow-card border border-border p-6 sm:p-8 space-y-6">

        {/* --- Required fields --- */}
        <div className="space-y-5">
          <div>
            <label htmlFor="jurisdiction" className={LABEL_CLASS}>
              Jurisdiction <span className="text-danger">*</span>
            </label>
            <div className="relative">
              <select
                id="jurisdiction"
                value={jurisdiction}
                onChange={(e) => {
                  setJurisdiction(e.target.value as Jurisdiction | "");
                  setZoningDistrict("");
                  setHeightDistrict("");
                  setOnPeninsula(false);
                }}
                className={INPUT_CLASS + " appearance-none pr-10 cursor-pointer"}
              >
                <option value="" disabled>Select jurisdiction</option>
                <optgroup label="Full Analysis (Solver + AI)">
                  {TIER_1_JURISDICTIONS.map((j) => (
                    <option key={j.value} value={j.value}>{j.label}</option>
                  ))}
                </optgroup>
                <optgroup label="Research-Backed (AI + Verified Data)">
                  {TIER_2_JURISDICTIONS.map((j) => (
                    <option key={j.value} value={j.value}>{j.label}</option>
                  ))}
                </optgroup>
                <optgroup label="Preliminary (AI-Only)">
                  {TIER_3_JURISDICTIONS.map((j) => (
                    <option key={j.value} value={j.value}>{j.label}</option>
                  ))}
                </optgroup>
              </select>
              <svg className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            {/* Tier notes */}
            {tier === 3 && (
              <div className="mt-2 flex items-start gap-2 text-xs text-warning bg-amber-50 rounded-btn px-3 py-2 border border-amber-200/60 animate-fadeIn">
                <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
                <span>Zoning data for this jurisdiction has not been independently verified. Analysis will include disclaimers.</span>
              </div>
            )}
            {tier === 2 && (
              <div className="mt-2 flex items-start gap-2 text-xs text-accent bg-accent-light rounded-btn px-3 py-2 border border-accent/20 animate-fadeIn">
                <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
                </svg>
                <span>AI-assisted analysis based on validated research data.</span>
              </div>
            )}
          </div>

          <div>
            <label htmlFor="address" className={LABEL_CLASS}>
              Address or TMS # <span className="text-danger">*</span>
            </label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter street address or TMS number"
              className={INPUT_CLASS}
            />
          </div>

          {/* Zoning District — Tier 1 required */}
          {tier === 1 && (
            <div className="animate-fadeIn">
              <label htmlFor="zoningDistrict" className={LABEL_CLASS}>
                Zoning District <span className="text-danger">*</span>
              </label>
              <input
                id="zoningDistrict"
                type="text"
                value={zoningDistrict}
                onChange={(e) => setZoningDistrict(e.target.value)}
                placeholder="e.g., MU-2, SR-1, GB, UC-OD"
                className={INPUT_CLASS}
              />
              <p className="mt-1 text-xs text-muted">
                Check your zoning at{" "}
                <a
                  href={jurisdiction === "charleston"
                    ? "https://charleston-sc.gov/GIS"
                    : "https://www.tompsc.com/gis"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline"
                >
                  {jurisdiction === "charleston" ? "charleston-sc.gov/GIS" : "tompsc.com/gis"}
                </a>
              </p>
            </div>
          )}

          {/* Height District — Charleston only */}
          {jurisdiction === "charleston" && (
            <div className="animate-fadeIn">
              <label htmlFor="heightDistrict" className={LABEL_CLASS}>
                Height District
              </label>
              <input
                id="heightDistrict"
                type="text"
                value={heightDistrict}
                onChange={(e) => setHeightDistrict(e.target.value)}
                placeholder="e.g., 4, 6, 4-12, 85/200"
                className={INPUT_CLASS}
              />
            </div>
          )}

          {/* On Peninsula toggle — Charleston only */}
          {jurisdiction === "charleston" && (
            <div className="flex items-center justify-between animate-fadeIn">
              <label htmlFor="onPeninsula" className="text-sm font-medium text-navy">
                On Peninsula?
              </label>
              <button
                id="onPeninsula"
                type="button"
                role="switch"
                aria-checked={onPeninsula}
                onClick={() => setOnPeninsula(!onPeninsula)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200
                  ${onPeninsula ? "bg-accent" : "bg-gray-300"}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200
                    ${onPeninsula ? "translate-x-6" : "translate-x-1"}`}
                />
              </button>
            </div>
          )}

          {/* Zoning District — optional for Tier 2/3 */}
          {(tier === 2 || tier === 3) && (
            <div className="animate-fadeIn">
              <label htmlFor="zoningDistrictOptional" className={LABEL_CLASS}>
                Zoning District <span className="text-muted font-normal">(optional)</span>
              </label>
              <input
                id="zoningDistrictOptional"
                type="text"
                value={zoningDistrict}
                onChange={(e) => setZoningDistrict(e.target.value)}
                placeholder="Enter if known — AI will infer if left blank"
                className={INPUT_CLASS}
              />
            </div>
          )}
        </div>

        {/* --- Optional section toggle --- */}
        <button
          type="button"
          onClick={() => setShowOptional(!showOptional)}
          className="flex items-center gap-2 text-sm font-medium text-accent hover:text-accent/80 transition-colors group"
        >
          <svg
            className={`w-4 h-4 transition-transform duration-200 ${showOptional ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          <span className="group-hover:underline underline-offset-2">Tell us more for a deeper analysis</span>
        </button>

        {/* --- Optional fields --- */}
        {showOptional && (
          <div className="space-y-5 pt-3 border-t border-border animate-slideDown">
            <div>
              <label htmlFor="lotSize" className={LABEL_CLASS}>
                Lot size
              </label>
              <input
                id="lotSize"
                type="text"
                value={lotSizeInput}
                onChange={(e) => setLotSizeInput(e.target.value)}
                placeholder="e.g., 8,500 SF or 0.2 acres"
                className={INPUT_CLASS}
              />
            </div>

            <div>
              <label className={LABEL_CLASS}>
                What are you considering?
              </label>
              <div className="flex flex-wrap gap-2">
                {USE_TYPE_OPTIONS.map((opt) => {
                  const selected = selectedUseTypes.has(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleUseType(opt.value)}
                      className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition-all duration-150
                        ${selected
                          ? "bg-accent text-white shadow-btn scale-[1.02]"
                          : "bg-white text-muted border border-border hover:border-accent/40 hover:text-navy"
                        }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label htmlFor="scale" className={LABEL_CLASS}>
                Approximate scale
              </label>
              <input
                id="scale"
                type="text"
                value={approximateScale}
                onChange={(e) => setApproximateScale(e.target.value)}
                placeholder="e.g., 40 units, 6 stories, 25,000 SF"
                className={INPUT_CLASS}
              />
            </div>

            <div>
              <label htmlFor="conditions" className={LABEL_CLASS}>
                Existing conditions
              </label>
              <input
                id="conditions"
                type="text"
                value={existingConditions}
                onChange={(e) => setExistingConditions(e.target.value)}
                placeholder="e.g., vacant lot, 1920s warehouse, single-family home"
                className={INPUT_CLASS}
              />
            </div>

            <div>
              <label htmlFor="context" className={LABEL_CLASS}>
                Additional context
              </label>
              <textarea
                id="context"
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                placeholder="Debating demolition vs. renovation, client constraints, timeline..."
                rows={3}
                className={INPUT_CLASS + " h-auto py-3 resize-y"}
              />
            </div>
          </div>
        )}

        {/* --- Error --- */}
        {error && (
          <div className="rounded-btn bg-red-50 border border-danger/20 px-4 py-3 text-sm text-danger flex items-start gap-3 animate-fadeIn">
            <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">{error}</div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-danger/50 hover:text-danger transition-colors flex-shrink-0"
              aria-label="Dismiss error"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* --- Submit --- */}
        <button
          type="submit"
          disabled={!canSubmit}
          className={`w-full h-12 rounded-btn text-white font-semibold text-sm transition-all duration-150
            ${canSubmit
              ? "bg-navy hover:bg-navy/90 hover:-translate-y-px hover:shadow-card-hover active:translate-y-0 cursor-pointer"
              : "bg-navy/30 cursor-not-allowed"
            }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2.5">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Analyzing parcel...
            </span>
          ) : (
            "Run Feasibility Analysis"
          )}
        </button>
      </div>
    </form>
  );
}
