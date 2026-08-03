import React, { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, Navigate, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  FileText,
  CheckSquare,
  Calculator,
  FileSpreadsheet,
  Search,
  Settings as SettingsIcon,
  User,
  LogOut,
  ChevronDown,
  Database,
  Activity,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/companies', label: 'Danh sách Công ty', icon: Building2 },
  { to: '/financials', label: 'Báo cáo Tài chính', icon: FileText },
  { to: '/normalization', label: 'Chuẩn hóa & Làm sạch', icon: CheckSquare },
  { to: '/ratios', label: 'Chỉ số Tài chính', icon: Calculator },
  // { to: '/distress', label: 'Gán nhãn Distress', icon: ShieldAlert },
  // { to: '/ai-studio', label: 'AI/ML Studio', icon: Cpu },
  // { to: '/prediction', label: 'Dự báo Rủi ro AI', icon: Sparkles },
  { to: '/explorer', label: 'Data Explorer', icon: Search },
  { to: '/dataset', label: 'Xuất Dataset', icon: FileSpreadsheet },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export const AppLayout: React.FC = () => {
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);
  const username = useAppStore((s) => s.username);
  const logout = useAppStore((s) => s.logout);
  const datasetCount = useAppStore((s) => s.datasetCount);
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────── */}
      <aside className="w-60 flex-shrink-0 bg-white border-r border-slate-200/80 flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-slate-100">
          <span className="fsd-logo text-xl">FSD //</span>
          <p className="text-[10px] font-medium text-slate-400 mt-0.5 tracking-widest uppercase">Data Lake Terminal</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive ? 'nav-link-active' : 'nav-link-idle'
                }`
              }
            >
              <Icon size={16} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="px-4 py-3 border-t border-slate-100">
          <div className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg bg-slate-50 border border-slate-200/60">
            <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 shadow-sm">
              <span className="text-white text-xs font-bold">{username?.charAt(0).toUpperCase() || 'U'}</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-800 truncate">{username}</p>
              <p className="text-[10px] text-emerald-600 font-medium">● Online / Admin</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 bg-white border-b border-slate-200/80 flex items-center justify-between px-6 flex-shrink-0">
          {/* Memory indicator */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3.5 py-1.5">
              <Database size={13} className="text-indigo-500" strokeWidth={2.5} />
              <span className="text-xs font-medium text-slate-500">SESSION MEMORY</span>
              <span className="text-xs font-bold text-indigo-600 ml-0.5">{datasetCount} Datasets</span>
            </div>
            <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-1.5">
              <Activity size={11} className="text-emerald-500" strokeWidth={2.5} />
              <span className="text-[11px] font-semibold text-emerald-600">Live</span>
            </div>
          </div>

          {/* Account dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((p) => !p)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-700
                hover:bg-slate-50 hover:border-slate-300 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-1"
            >
              <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center">
                <User size={12} className="text-white" />
              </div>
              <span>{username}</span>
              <ChevronDown size={13} className={`text-slate-400 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-60 bg-white rounded-xl border border-slate-200 shadow-lg shadow-slate-200/50 z-50 overflow-hidden">
                <div className="px-4 py-3.5 bg-gradient-to-br from-indigo-50 to-slate-50 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center">
                      <span className="text-white font-bold text-sm">{username?.charAt(0).toUpperCase() || 'U'}</span>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{username}</p>
                      <p className="text-xs text-slate-500">admin@fsd-terminal.com</p>
                    </div>
                  </div>
                </div>

                <div className="px-4 py-3 border-b border-slate-100">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Terminal ID</span>
                    <span className="font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">#X9-FSD</span>
                  </div>
                </div>

                <div className="p-2">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-red-600
                      hover:bg-red-50 transition-all duration-150 group"
                  >
                    <LogOut size={14} className="group-hover:translate-x-0.5 transition-transform duration-150" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
