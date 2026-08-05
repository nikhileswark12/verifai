interface ResearchErrorProps {
  error: string | null;
  onRetry?: () => void;
}

export function ResearchError({ error, onRetry }: ResearchErrorProps) {
  if (!error) return null;

  return (
    <div className="bg-rose-50 border border-rose-200 rounded-lg p-6 flex flex-col items-start gap-4">
      <div>
        <h4 className="text-rose-800 font-semibold text-lg">Analysis Failed</h4>
        <p className="text-rose-600 mt-1">{error}</p>
      </div>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-rose-100 hover:bg-rose-200 text-rose-700 font-medium rounded-md transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
