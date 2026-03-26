import { useEffect, useState } from "react";
import StatusIndicator from "./components/StatusIndicator";
import { checkHealth } from "./api/client";

export default function App() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold tracking-tight text-navy">
          Parcel<span className="text-accent">IQ</span>.ai
        </h1>
        <p className="text-lg text-navy/70">
          Development Feasibility Intelligence for Charleston County
        </p>
        <div className="pt-4 flex justify-center">
          <StatusIndicator connected={connected} />
        </div>
      </div>
    </div>
  );
}
