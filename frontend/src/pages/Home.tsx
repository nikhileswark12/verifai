import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";

export function Home() {
  return (
    <div className="flex flex-col min-h-[80vh]">
      {/* Hero Section */}
      <section className="flex flex-col items-center justify-center text-center py-20 px-4 md:px-8 bg-slate-50 border-b border-slate-200">
        <div className="space-y-6 max-w-3xl">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight">
            VerifAI
          </h1>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-700">
            Autonomous AI Research and Fact Verification Platform
          </h2>
          <p className="text-lg md:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Research claims using multi-agent AI verification. Submit queries to automatically gather evidence, verify claims, and detect contradictions.
          </p>
          <div className="flex justify-center pt-8">
            <Link to="/research">
              <Button size="lg" variant="primary" className="px-8 py-4 text-lg">
                Start Research
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Overview */}
      <section className="py-20 px-4 md:px-8 max-w-6xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left space-y-4">
          <div className="bg-blue-100 text-blue-800 p-3 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-900">Multi-Agent Research</h3>
          <p className="text-slate-600 leading-relaxed">
            Our pipeline utilizes specialized agents (Planner, Researcher, Verifier, Reporter) working in concert to break down complex queries and conduct thorough investigations.
          </p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left space-y-4">
          <div className="bg-emerald-100 text-emerald-800 p-3 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-900">Evidence Verification</h3>
          <p className="text-slate-600 leading-relaxed">
            Every claim is cross-referenced against multiple high-quality sources. We automatically classify source reliability to ensure conclusions are built on trusted data.
          </p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left space-y-4">
          <div className="bg-amber-100 text-amber-800 p-3 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-900">Confidence Analysis</h3>
          <p className="text-slate-600 leading-relaxed">
            Results are presented with granular confidence scores based on source reliability, evidence agreement, and citation completeness, giving you a clear picture of certainty.
          </p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start text-left space-y-4">
          <div className="bg-rose-100 text-rose-800 p-3 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-slate-900">Contradiction Detection</h3>
          <p className="text-slate-600 leading-relaxed">
            The system automatically identifies and highlights conflicting information across sources, detailing whether disagreements are direct, temporal, or contextual.
          </p>
        </div>
      </section>
    </div>
  );
}
