interface StatusIndicatorProps {
  connected: boolean | null;
}

export default function StatusIndicator({ connected }: StatusIndicatorProps) {
  if (connected === null) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <div className="w-2.5 h-2.5 rounded-full bg-gray-300 animate-pulse" />
        Connecting...
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 text-sm ${connected ? "text-emerald-600" : "text-red-500"}`}>
      <div className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-emerald-500" : "bg-red-500"}`} />
      {connected ? "Backend connected" : "Backend unreachable"}
    </div>
  );
}
