interface ConfidenceBarProps {
  score: number;
}

export function ConfidenceBar({ score }: ConfidenceBarProps) {
  const safeScore = Math.max(0, Math.min(100, Math.round(score)));
  
  let colorClass = "bg-slate-300";
  if (safeScore >= 80) colorClass = "bg-emerald-500";
  else if (safeScore >= 50) colorClass = "bg-amber-500";
  else colorClass = "bg-rose-500";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-grow h-2 bg-slate-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClass} transition-all duration-500 ease-out`}
          style={{ width: `${safeScore}%` }}
        />
      </div>
      <span className="text-sm font-bold text-slate-700 min-w-[3ch]">{safeScore}%</span>
    </div>
  );
}
