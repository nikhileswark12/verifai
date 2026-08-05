import { useState } from "react";
import { Button } from "../ui/Button";

interface ResearchFormProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="query" className="block text-sm font-medium text-slate-700 mb-2">
          What would you like to investigate?
        </label>
        <textarea
          id="query"
          rows={4}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          placeholder="e.g. Enter a claim, question, or topic to research..."
          className="w-full p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-slate-50 disabled:text-slate-500 text-slate-900 placeholder:text-slate-400"
        />
      </div>
      <div className="flex justify-end">
        <Button
          type="submit"
          variant="primary"
          disabled={!query.trim() || isLoading}
        >
          {isLoading ? "Submitting..." : "Start Research"}
        </Button>
      </div>
    </form>
  );
}
