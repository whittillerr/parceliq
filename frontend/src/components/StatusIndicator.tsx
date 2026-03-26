interface StatusIndicatorProps {
  connected: boolean | null;
}

export default function StatusIndicator({ connected }: StatusIndicatorProps) {
  if (connected === null) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted">
        <div className="w-2 h-2 rounded-full bg-gray-300 animate-pulse" />
        <span className="hidden sm:inline">Connecting...</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 text-xs font-medium ${connected ? "text-success" : "text-danger"}`}>
      <div className={`w-2 h-2 rounded-full ${connected ? "bg-success" : "bg-danger"}`} />
      <span className="hidden sm:inline">{connected ? "Connected" : "Offline"}</span>
    </div>
  );
}
