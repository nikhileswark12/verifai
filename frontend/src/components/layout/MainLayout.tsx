
import { Outlet, Link } from "react-router-dom";

export function MainLayout() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Link to="/" className="text-xl font-bold tracking-tight text-slate-900 hover:text-blue-600 transition-colors">
            VerifAI
          </Link>
          <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 text-xs font-semibold ml-2">
            Research Platform
          </span>
        </div>
        <nav className="flex gap-4 text-sm font-medium">
          <Link to="/" className="text-slate-600 hover:text-slate-900">Home</Link>
          <Link to="/research" className="text-slate-600 hover:text-slate-900">Workspace</Link>
        </nav>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto p-6 md:p-8">
        <Outlet />
      </main>
      
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-500">
        <p>&copy; {new Date().getFullYear()} VerifAI Research. All rights reserved.</p>
      </footer>
    </div>
  );
}
