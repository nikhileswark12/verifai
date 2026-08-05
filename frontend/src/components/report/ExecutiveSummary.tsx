interface ExecutiveSummaryProps {
  summary?: string;
}

export function ExecutiveSummary({ summary }: ExecutiveSummaryProps) {
  if (!summary) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2">
        Executive Summary
      </h2>
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
          {summary}
        </p>
      </div>
    </div>
  );
}
