import { useEffect, useRef, useState } from "react";
import StatusIndicator from "./components/StatusIndicator";
import AnalysisForm from "./components/AnalysisForm";
import AnalysisResults from "./components/AnalysisResults";
import { checkHealth } from "./api/client";
import type { AnalysisResponse } from "./types/analysis";

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
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
    }, 100);
  }

  return (
    <div className="min-h-screen bg-[#F7FAFC]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-navy">
              Parcel<span className="text-accent">IQ</span>.ai
            </h1>
            <p className="text-sm text-navy/60 mt-0.5">
              Development Feasibility Intelligence for Charleston County
            </p>
          </div>
          <StatusIndicator connected={connected} />
        </div>
      </header>

      {/* Main */}
      <main className="max-w-4xl mx-auto px-4 py-10 space-y-8">
        <AnalysisForm onAnalysisComplete={handleAnalysisComplete} />

        {result && (
          <div ref={resultsRef}>
            <AnalysisResults data={result} />
          </div>
        )}
      </main>
    </div>
  );
}
