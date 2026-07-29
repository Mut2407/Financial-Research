import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format, subDays } from 'date-fns';
import {
  TrendingUp,
  TrendingDown,
  BarChart2,
  Activity,
  Calendar,
  ChevronDown,
  RefreshCw,
  ServerCrash,
  Info,
  Eye,
  EyeOff,
} from 'lucide-react';
import {
  XAxis, YAxis, CartesianGrid, Line,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend, Area, AreaChart,
} from 'recharts';
import { getCompanies, getPrices } from '../../services/api';
import type { Company, PriceData } from '../../types';

// ── Skeleton ──────────────────────────────────────────────────
const MetricSkeleton = () => (
  <div className="metric-card space-y-3">
    <div className="skeleton h-3 w-24" />
    <div className="skeleton h-7 w-32" />
    <div className="skeleton h-3 w-16" />
  </div>
);

// ── Metric Card ───────────────────────────────────────────────
interface MetricCardProps {
  label: string;
  value: string;
  delta?: number;
  icon: React.ReactNode;
  prefix?: string;
}
const MetricCard: React.FC<MetricCardProps> = ({ label, value, delta, icon, prefix }) => {
  const isPositive = delta !== undefined && delta >= 0;
  return (
    <div className="metric-card group">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-100 transition-colors duration-200">
          {icon}
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-900 tracking-tight">
        {prefix && <span className="text-slate-400 text-lg font-medium">{prefix}</span>}
        {value}
      </div>
      {delta !== undefined && (
        <div className={`mt-1.5 flex items-center gap-1 text-xs font-semibold ${isPositive ? 'text-emerald-600' : 'text-red-500'}`}>
          {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {delta > 0 ? '+' : ''}{delta.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} so với phiên trước
        </div>
      )}
    </div>
  );
};

// ── Custom Tooltip ────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50 p-3 text-sm">
      <p className="font-semibold text-slate-600 mb-2">{format(new Date(label as string), 'dd/MM/yyyy')}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            {entry.name}
          </span>
          <span className="font-bold text-slate-800">{entry.value?.toLocaleString('vi-VN')}</span>
        </div>
      ))}
    </div>
  );
};

// ── Main Dashboard ────────────────────────────────────────────
export const Dashboard: React.FC = () => {
  const [selectedTicker, setSelectedTicker] = useState('');
  const [useFilter, setUseFilter] = useState(false);
  const [startDate, setStartDate] = useState(format(subDays(new Date(), 90), 'yyyy-MM-dd'));
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [showChart, setShowChart] = useState(true);
  const [showTable, setShowTable] = useState(false);

  const {
    data: companiesData, isLoading: isLoadingCompanies, isError: isErrorCompanies, refetch: refetchCompanies,
  } = useQuery({ queryKey: ['companies'], queryFn: () => getCompanies(100) });

  const companies: Company[] = companiesData?.data ?? [];

  useEffect(() => {
    if (companies.length > 0 && !selectedTicker) {
      setSelectedTicker(companies[0].ticker);
    }
  }, [companies, selectedTicker]);

  const {
    data: pricesData, isLoading: isLoadingPrices, isError: isErrorPrices,
  } = useQuery({
    queryKey: ['prices', selectedTicker, useFilter ? startDate : undefined, useFilter ? endDate : undefined],
    queryFn: () => getPrices(selectedTicker, useFilter ? startDate : undefined, useFilter ? endDate : undefined, 1000),
    enabled: !!selectedTicker,
    staleTime: 30_000,
  });

  const prices: PriceData[] = pricesData?.data ?? [];
  const latest = prices.at(-1);
  const prev = prices.at(-2);
  const priceDiff = latest && prev ? latest.close_price - prev.close_price : 0;

  // ── Error: companies ──
  if (isErrorCompanies) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 space-y-4">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
          <ServerCrash size={28} className="text-red-400" />
        </div>
        <div className="text-center">
          <h3 className="font-semibold text-slate-800">Không thể kết nối Backend</h3>
          <p className="text-sm text-slate-500 mt-1">Kiểm tra Backend tại <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">http://localhost:8000</code></p>
        </div>
        <button onClick={() => refetchCompanies()} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} /> Thử lại
        </button>
      </div>
    );
  }

  // ── Empty: companies ──
  if (!isLoadingCompanies && companies.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 space-y-4">
        <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center">
          <Info size={28} className="text-amber-400" />
        </div>
        <div className="text-center">
          <h3 className="font-semibold text-slate-800">Chưa có dữ liệu</h3>
          <p className="text-sm text-slate-500 mt-1">Hãy chạy ingestion trong <strong>Data Explorer</strong> trước.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Curated Market Data — FastAPI → DuckDB → Parquet</p>
        </div>
      </div>

      {/* ── Control Panel ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-end gap-4">
          {/* Ticker select */}
          <div className="flex-1 space-y-1.5">
            <label className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Mã chứng khoán</label>
            {isLoadingCompanies ? (
              <div className="skeleton h-10 w-full" />
            ) : (
              <div className="relative">
                <select
                  className="input-field appearance-none pr-9 cursor-pointer"
                  value={selectedTicker}
                  onChange={(e) => setSelectedTicker(e.target.value)}
                >
                  {companies.map((c) => (
                    <option key={c.ticker} value={c.ticker}>
                      {c.ticker} — {c.name || 'N/A'}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
            )}
          </div>

          {/* Date filter toggle */}
          <div className="flex items-center gap-2 pb-1">
            <button
              onClick={() => setUseFilter((p) => !p)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium border transition-all duration-150 ${
                useFilter
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Calendar size={14} />
              {useFilter ? 'Lọc ngày: Bật' : 'Lọc theo ngày'}
            </button>
          </div>
        </div>

        {/* Date range */}
        {useFilter && (
          <div className="grid grid-cols-2 gap-4 pt-1 border-t border-slate-100">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-500">Từ ngày</label>
              <input type="date" className="input-field" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-500">Đến ngày</label>
              <input type="date" className="input-field" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
            {new Date(startDate) > new Date(endDate) && (
              <p className="col-span-2 text-xs text-red-500 font-medium flex items-center gap-1">
                <Info size={12} /> Từ ngày phải nhỏ hơn hoặc bằng đến ngày.
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── Metrics ── */}
      {isLoadingPrices ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <MetricSkeleton key={i} />)}
        </div>
      ) : isErrorPrices ? (
        <div className="bg-red-50 border border-red-100 rounded-xl p-4 text-sm text-red-600 flex items-center gap-2">
          <ServerCrash size={16} /> Không thể tải dữ liệu giá. Vui lòng thử lại.
        </div>
      ) : prices.length === 0 ? (
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-600 flex items-center gap-2">
          <Info size={16} /> Không có dữ liệu trong khoảng thời gian này.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="Giá đóng cửa" value={latest?.close_price.toLocaleString('vi-VN') ?? '—'} delta={priceDiff} icon={<TrendingUp size={15} />} />
            <MetricCard label="Khối lượng" value={latest?.volume.toLocaleString('vi-VN') ?? '—'} icon={<BarChart2 size={15} />} />
            <MetricCard label="MA 20" value={latest?.ma20 != null ? latest.ma20.toLocaleString('vi-VN', { maximumFractionDigits: 2 }) : 'N/A'} icon={<Activity size={15} />} />
            <MetricCard label="RSI 14" value={latest?.rsi_14 != null ? latest.rsi_14.toFixed(2) : 'N/A'} icon={<Activity size={15} />} />
          </div>

          {/* ── Chart ── */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">Biểu đồ phân tích kỹ thuật — {selectedTicker}</h2>
                <p className="text-xs text-slate-400 mt-0.5">{prices.length} phiên giao dịch</p>
              </div>
              <button
                onClick={() => setShowChart((p) => !p)}
                className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors"
              >
                {showChart ? <><EyeOff size={13} /> Ẩn</> : <><Eye size={13} /> Hiện</>}
              </button>
            </div>
            {showChart && (
              <div className="p-5 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={prices} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis
                      dataKey="trading_date"
                      tickFormatter={(v) => format(new Date(v as string), 'dd/MM')}
                      tick={{ fontSize: 11, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      tick={{ fontSize: 11, fill: '#94a3b8' }}
                      axisLine={false}
                      tickLine={false}
                      width={55}
                    />
                    <RechartsTooltip content={<CustomTooltip />} />
                    <Legend
                      wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }}
                      iconType="circle"
                      iconSize={8}
                    />
                    <Area type="monotone" dataKey="close_price" name="Close Price" stroke="#6366f1" strokeWidth={2} fill="url(#colorClose)" dot={false} activeDot={{ r: 4 }} />
                    <Line type="monotone" dataKey="ma20" name="MA20" stroke="#f59e0b" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* ── Data Table ── */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
            <button
              onClick={() => setShowTable((p) => !p)}
              className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <span>Dữ liệu Curated ({prices.length} dòng)</span>
              <ChevronDown size={15} className={`text-slate-400 transition-transform duration-200 ${showTable ? 'rotate-180' : ''}`} />
            </button>
            {showTable && (
              <div className="border-t border-slate-100 overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr>
                      {['Ngày', 'Mở cửa', 'Cao nhất', 'Thấp nhất', 'Đóng cửa', 'Khối lượng', 'MA20', 'RSI 14'].map((h) => (
                        <th key={h} className="table-header whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {prices.slice(-30).reverse().map((p, i) => (
                      <tr key={i} className="table-row">
                        <td className="table-cell font-medium text-slate-600">{format(new Date(p.trading_date), 'dd/MM/yyyy')}</td>
                        <td className="table-cell text-right">{p.open_price.toLocaleString('vi-VN')}</td>
                        <td className="table-cell text-right text-emerald-600 font-medium">{p.high_price.toLocaleString('vi-VN')}</td>
                        <td className="table-cell text-right text-red-500 font-medium">{p.low_price.toLocaleString('vi-VN')}</td>
                        <td className="table-cell text-right font-semibold text-slate-800">{p.close_price.toLocaleString('vi-VN')}</td>
                        <td className="table-cell text-right">{p.volume.toLocaleString('vi-VN')}</td>
                        <td className="table-cell text-right text-amber-600">{p.ma20 != null ? p.ma20.toFixed(0) : '—'}</td>
                        <td className="table-cell text-right">{p.rsi_14 != null ? p.rsi_14.toFixed(2) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400 text-center">
                  Hiển thị 30 phiên gần nhất
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
