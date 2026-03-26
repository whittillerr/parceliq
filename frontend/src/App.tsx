import { useEffect, useState } from "react";
import StatusIndicator from "./components/StatusIndicator";
import AnalysisForm from "./components/AnalysisForm";
import { checkHealth } from "./api/client";
import type { AnalysisResponse } from "./types/analysis";

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [_result, setResult] = useState<AnalysisResponse | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

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
        <AnalysisForm onAnalysisComplete={(response) => setResult(response)} />

        {/* Results placeholder */}
        {_result ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-navy/50">
            Analysis results will appear here
          </div>
        ) : null}
      </main>
    </div>
  );
}
