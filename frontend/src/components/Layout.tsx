import { Link, Outlet, useNavigate } from "react-router-dom";
import { auth } from "../api";

export default function Layout() {
  const nav = useNavigate();
  const logout = () => { auth.clear(); nav("/login"); };
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="font-bold text-lg">Theo Anold — Guard Dashboard</h1>
          <nav className="flex gap-4 text-sm">
            <Link to="/" className="hover:text-white">Live</Link>
            <Link to="/reports" className="hover:text-white">Reports</Link>
          </nav>
        </div>
        <div className="text-sm text-slate-400">
          {auth.name} · {auth.role}
          <button onClick={logout} className="ml-4 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700">
            Log out
          </button>
        </div>
      </header>
      <main className="flex-1 p-6"><Outlet /></main>
    </div>
  );
}
