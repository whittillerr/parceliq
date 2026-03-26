import { useEffect, useRef, useState } from "react";
import StatusIndicator from "./components/StatusIndicator";
import AnalysisForm from "./components/AnalysisForm";
import AnalysisResults from "./components/AnalysisResults";
import { checkHealth } from "./api/client";
import type { AnalysisResponse } from "./types/analysis";

/* ---------- Loading skeleton ---------- */

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Progress card */}
      <div className="bg-white rounded-card shadow-card border border-border p-6 animate-fadeIn">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-accent-light flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-semibold text-navy">Running feasibility analysis...</p>
            <p className="text-xs text-muted mt-0.5">Constraint solver + AI intelligence layers</p>
          </div>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
          <div className="bg-accent h-1.5 rounded-full animate-[progress_12s_ease-in-out_forwards]" />
        </div>
      </div>

      {/* Skeleton envelope */}
      <div className="bg-white rounded-card shadow-card border border-border overflow-hidden animate-pulse">
        <div className="bg-navy px-6 py-3.5">
          <div className="h-4 w-44 bg-white/20 rounded" />
        </div>
        <div className="p-6 space-y-4">
          <div className="flex gap-3">
            <div className="h-7 w-16 bg-accent-light rounded-full" />
            <div className="h-4 w-48 bg-gray-100 rounded mt-1.5" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3 space-y-2">
                <div className="h-3 w-14 bg-gray-200 rounded" />
                <div className="h-4 w-20 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Skeleton scenarios */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-card shadow-card border border-border p-5 space-y-3">
            <div className="flex justify-between">
              <div className="h-4 w-20 bg-gray-200 rounded" />
              <div className="h-5 w-14 bg-gray-100 rounded-full" />
            </div>
            <div className="h-3 w-full bg-gray-100 rounded" />
            <div className="h-3 w-3/4 bg-gray-100 rounded" />
            <div className="h-3 w-1/2 bg-gray-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------- Footer ---------- */

function SiteFooter() {
  return (
    <footer className="border-t border-border bg-white mt-16">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Cross-product links */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
          <a
            href="https://georgest.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-3 bg-gray-50 hover:bg-accent-light rounded-card p-4 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent text-sm font-bold flex-shrink-0 group-hover:bg-accent group-hover:text-white transition-colors">
              G
            </div>
            <div>
              <div className="text-sm font-medium text-navy">GeorgeSt.ai</div>
              <div className="text-xs text-muted">Permit Pre-Flight</div>
            </div>
          </a>
          <a
            href="https://halfdays.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-3 bg-gray-50 hover:bg-accent-light rounded-card p-4 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent text-sm font-bold flex-shrink-0 group-hover:bg-accent group-hover:text-white transition-colors">
              H
            </div>
            <div>
              <div className="text-sm font-medium text-navy">Halfdays</div>
              <div className="text-xs text-muted">AI Strategy for Real Estate</div>
            </div>
          </a>
        </div>

        {/* Bottom row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted">
          <div className="font-medium">
            ParcelIQ.ai &copy; {new Date().getFullYear()} Halfdays AI
          </div>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-navy transition-colors">Privacy</a>
            <span className="text-border">|</span>
            <a href="#" className="hover:text-navy transition-colors">Terms</a>
            <span className="text-border">|</span>
            <a href="mailto:only@halfdays.ai" className="hover:text-navy transition-colors">only@halfdays.ai</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ---------- App ---------- */

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  function handleAnalysisComplete(response: AnalysisResponse) {
    setResult(response);
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
  }

  function handleNewAnalysis() {
    setResult(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#F7FAFC]">
      {/* Header */}
      <header className="bg-white border-b border-border sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-navy">
              Parcel<span className="text-accent">IQ</span><span className="text-navy/40">.ai</span>
            </h1>
            <span className="hidden sm:inline text-xs text-muted font-medium">by Halfdays AI</span>
          </div>
          <StatusIndicator connected={connected} />
        </div>
      </header>

      {/* Tagline */}
      <div className="bg-white border-b border-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 pb-4 pt-0.5">
          <p className="text-sm text-muted">
            Development Feasibility Intelligence for Charleston County
          </p>
        </div>
      </div>

      {/* Main */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8">
        <AnalysisForm
          onAnalysisComplete={handleAnalysisComplete}
          onLoadingChange={setLoading}
        />

        {/* Loading skeleton */}
        {loading && !result && (
          <div ref={resultsRef}>
            <LoadingSkeleton />
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div ref={resultsRef} className="stagger-children">
            <AnalysisResults data={result} />

            {/* New Analysis button */}
            <div className="flex justify-center pt-8 animate-fadeIn" style={{ animationDelay: "500ms" }}>
              <button
                onClick={handleNewAnalysis}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-btn border border-border
                           text-navy font-medium text-sm bg-white hover:bg-gray-50 hover:shadow-card
                           transition-all shadow-btn"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                New Analysis
              </button>
            </div>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
