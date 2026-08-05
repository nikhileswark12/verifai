interface ReferenceListProps {
  references?: string[];
}

export function ReferenceList({ references }: ReferenceListProps) {
  if (!references || references.length === 0) {
    return (
      <div className="p-8 text-center border border-slate-200 border-dashed rounded-xl bg-slate-50">
        <p className="text-slate-500 font-medium">No references available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <ul className="space-y-3">
        {references.map((url, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="text-slate-400 font-mono text-sm mt-0.5">{index + 1}.</span>
            <a 
              href={url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline text-sm break-all"
            >
              {url}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
