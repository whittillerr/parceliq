import { useState } from "react";
import type { AnalysisRequest, AnalysisResponse, Jurisdiction, UseType } from "../types/analysis";
import { analyzeParcel } from "../api/client";

const JURISDICTIONS: { value: Jurisdiction; label: string }[] = [
  { value: "charleston", label: "City of Charleston" },
  { value: "mount_pleasant", label: "Mount Pleasant" },
  { value: "north_charleston", label: "North Charleston" },
  { value: "sullivans_island", label: "Sullivan's Island" },
  { value: "isle_of_palms", label: "Isle of Palms" },
  { value: "folly_beach", label: "Folly Beach" },
  { value: "james_island", label: "Town of James Island" },
  { value: "kiawah", label: "Kiawah Island" },
  { value: "summerville", label: "Summerville" },
  { value: "goose_creek", label: "Goose Creek" },
  { value: "hanahan", label: "Hanahan" },
  { value: "unincorporated", label: "Unincorporated Charleston County" },
];

const USE_TYPE_OPTIONS: { value: UseType | "unsure"; label: string }[] = [
  { value: "residential", label: "Residential" },
  { value: "commercial", label: "Commercial" },
  { value: "mixed_use", label: "Mixed-Use" },
  { value: "hospitality", label: "Hospitality" },
  { value: "adaptive_reuse", label: "Adaptive Reuse" },
  { value: "unsure", label: "Unsure" },
];

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

interface AnalysisFormProps {
  onAnalysisComplete: (response: AnalysisResponse) => void;
}

export default function AnalysisForm({ onAnalysisComplete }: AnalysisFormProps) {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction | "">("");
  const [address, setAddress] = useState("");
  const [lotSizeInput, setLotSizeInput] = useState("");
  const [selectedUseTypes, setSelectedUseTypes] = useState<Set<UseType | "unsure">>(new Set());
  const [approximateScale, setApproximateScale] = useState("");
  const [existingConditions, setExistingConditions] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [showOptional, setShowOptional] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = jurisdiction !== "" && address.trim() !== "" && !loading;

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
    setError(null);

    const useTypes = [...selectedUseTypes].filter((v): v is UseType => v !== "unsure");

    const request: AnalysisRequest = {
      jurisdiction: jurisdiction as Jurisdiction,
      address: address.trim(),
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
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8 space-y-6">

        {/* --- Required fields --- */}
        <div className="space-y-4">
          <div>
            <label htmlFor="jurisdiction" className="block text-sm font-medium text-navy mb-1.5">
              Jurisdiction <span className="text-red-400">*</span>
            </label>
            <select
              id="jurisdiction"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value as Jurisdiction | "")}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy bg-white
                         focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                         transition-colors"
            >
              <option value="" disabled>Select jurisdiction</option>
              {JURISDICTIONS.map((j) => (
                <option key={j.value} value={j.value}>{j.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="address" className="block text-sm font-medium text-navy mb-1.5">
              Address or TMS # <span className="text-red-400">*</span>
            </label>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter street address or TMS number"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy
                         placeholder:text-gray-400
                         focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                         transition-colors"
            />
          </div>
        </div>

        {/* --- Optional section toggle --- */}
        <button
          type="button"
          onClick={() => setShowOptional(!showOptional)}
          className="flex items-center gap-2 text-sm text-accent hover:text-accent/80 transition-colors"
        >
          <svg
            className={`w-4 h-4 transition-transform ${showOptional ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          Tell us more for a deeper analysis
        </button>

        {/* --- Optional fields --- */}
        {showOptional && (
          <div className="space-y-4 pt-2 border-t border-gray-100">
            <div>
              <label htmlFor="lotSize" className="block text-sm font-medium text-navy mb-1.5">
                Lot size
              </label>
              <input
                id="lotSize"
                type="text"
                value={lotSizeInput}
                onChange={(e) => setLotSizeInput(e.target.value)}
                placeholder="e.g., 8,500 SF or 0.2 acres"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy
                           placeholder:text-gray-400
                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                           transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-navy mb-2">
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
                      className={`px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors
                        ${selected
                          ? "bg-accent text-white"
                          : "bg-white text-navy/70 border border-gray-300 hover:border-accent/50"
                        }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label htmlFor="scale" className="block text-sm font-medium text-navy mb-1.5">
                Approximate scale
              </label>
              <input
                id="scale"
                type="text"
                value={approximateScale}
                onChange={(e) => setApproximateScale(e.target.value)}
                placeholder="e.g., 40 units, 6 stories, 25,000 SF"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy
                           placeholder:text-gray-400
                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                           transition-colors"
              />
            </div>

            <div>
              <label htmlFor="conditions" className="block text-sm font-medium text-navy mb-1.5">
                Existing conditions
              </label>
              <input
                id="conditions"
                type="text"
                value={existingConditions}
                onChange={(e) => setExistingConditions(e.target.value)}
                placeholder="e.g., vacant lot, 1920s warehouse, single-family home"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy
                           placeholder:text-gray-400
                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                           transition-colors"
              />
            </div>

            <div>
              <label htmlFor="context" className="block text-sm font-medium text-navy mb-1.5">
                Additional context
              </label>
              <textarea
                id="context"
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                placeholder="Anything else: debating demolition vs. renovation, client constraints, timeline concerns..."
                rows={3}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-navy
                           placeholder:text-gray-400 resize-y
                           focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent
                           transition-colors"
              />
            </div>
          </div>
        )}

        {/* --- Error --- */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* --- Submit --- */}
        <button
          type="submit"
          disabled={!canSubmit}
          className={`w-full rounded-lg py-3 text-white font-semibold text-base transition-colors
            ${canSubmit
              ? "bg-navy hover:bg-navy/90 cursor-pointer"
              : "bg-navy/40 cursor-not-allowed"
            }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
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
