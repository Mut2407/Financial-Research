import React from 'react';
import { Server, Paintbrush, Terminal, ShieldCheck } from 'lucide-react';

const settingItems = [
  {
    icon: <Server size={16} className="text-indigo-500" />,
    title: 'API Configuration',
    desc: 'Endpoint backend hiện tại',
    value: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    valueClass: 'font-mono text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md',
  },
  {
    icon: <Paintbrush size={16} className="text-violet-500" />,
    title: 'Theme',
    desc: 'Chế độ giao diện hiện tại',
    value: 'Light (Default)',
    valueClass: 'badge-slate',
  },
  {
    icon: <ShieldCheck size={16} className="text-emerald-500" />,
    title: 'Authentication',
    desc: 'Phương thức xác thực',
    value: 'Session Store (Zustand)',
    valueClass: 'badge-green',
  },
];

export const Settings: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Cấu hình hệ thống và tuỳ chọn giao diện.</p>
      </div>

      {/* Config items */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden divide-y divide-slate-100">
        {settingItems.map(({ icon, title, desc, value, valueClass }) => (
          <div key={title} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50/70 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                {icon}
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-700">{title}</p>
                <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
              </div>
            </div>
            <span className={valueClass}>{value}</span>
          </div>
        ))}
      </div>

      {/* Version card */}
      <div className="flex items-center gap-3 px-5 py-4 bg-slate-800 rounded-xl">
        <Terminal size={16} className="text-slate-400" />
        <div>
          <p className="text-xs font-semibold text-slate-300">FSD Terminal — React + Vite</p>
          <p className="text-xs text-slate-500 mt-0.5">v1.0.0 · TypeScript · TailwindCSS · React Query</p>
        </div>
      </div>
    </div>
  );
};
