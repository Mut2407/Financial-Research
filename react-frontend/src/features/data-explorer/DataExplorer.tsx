import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { format, subDays } from 'date-fns';
import { Play, CheckCircle2, XCircle, Info, ChevronDown, Loader2 } from 'lucide-react';
import { runPipeline, getPrices } from '../../services/api';
import type { PipelineResult, PriceData } from '../../types';

interface IngestionForm {
  tickerText: string;
  startDate: string;
  endDate: string;
  interval: string;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => (
  status === 'PASS'
    ? <span className="badge-green"><CheckCircle2 size={10} /> PASS</span>
    : <span className="badge-red"><XCircle size={10} /> FAIL</span>
);

export const DataExplorer: React.FC = () => {
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestedTickers, setIngestedTickers] = useState<string[]>([]);
  const [previewTicker, setPreviewTicker] = useState('');
  const [previewData, setPreviewData] = useState<PriceData[]>([]);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  const { register, handleSubmit } = useForm<IngestionForm>({
    defaultValues: {
      tickerText: 'FPT',
      startDate: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd'),
      interval: '1D',
    },
  });

  const onSubmit = async (data: IngestionForm) => {
    const tickers = data.tickerText.split(',').map((t) => t.trim().toUpperCase()).filter(Boolean);
    if (!tickers.length) return;
    if (new Date(data.startDate) > new Date(data.endDate)) return;

    setIsIngesting(true);
    setPipelineResult(null);
    try {
      const result = await runPipeline(tickers, data.startDate, data.endDate, data.interval);
      setPipelineResult(result);
      const passed = result.ingestion.details.filter((d: any) => d.status === 'PASS').map((d: any) => d.ticker);
      setIngestedTickers((prev) => Array.from(new Set([...prev, ...passed])));
      if (passed.length > 0 && !previewTicker) setPreviewTicker(passed[0]);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi gọi pipeline API.');
    } finally {
      setIsIngesting(false);
    }
  };

  useEffect(() => {
    if (!previewTicker) return;
    setIsLoadingPreview(true);
    getPrices(previewTicker, undefined, undefined, 100)
      .then((res) => setPreviewData(res.data ?? []))
      .catch(() => setPreviewData([]))
      .finally(() => setIsLoadingPreview(false));
  }, [previewTicker]);

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Header ── */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Data Explorer</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Live ingestion: Vnstock Free API → Raw JSON → Validation → Curated Parquet
        </p>
      </div>

      {/* ── Ingestion Form ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Play size={14} className="text-indigo-500" /> Cấu hình Ingestion
          </h2>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Ticker <span className="font-normal text-slate-400">(phân cách bằng dấu phẩy)</span>
            </label>
            <input
              {...register('tickerText')}
              placeholder="FPT, VNM, VCB, HPG..."
              className="input-field"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Từ ngày</label>
              <input type="date" {...register('startDate')} className="input-field" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Đến ngày</label>
              <input type="date" {...register('endDate')} className="input-field" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Interval</label>
              <div className="relative">
                <select {...register('interval')} className="input-field appearance-none pr-9 cursor-pointer">
                  <option value="1D">1D — Daily</option>
                </select>
                <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>

          <button type="submit" disabled={isIngesting} className="btn-primary w-full flex items-center justify-center gap-2">
            {isIngesting ? (
              <><Loader2 size={14} className="animate-spin" /> Đang gọi Vnstock API và ghi dữ liệu...</>
            ) : (
              <><Play size={14} /> Chạy Ingestion thật</>
            )}
          </button>
        </form>
      </div>

      {/* ── Info banner ── */}
      {!pipelineResult && !isIngesting && (
        <div className="flex items-start gap-3 bg-blue-50/60 border border-blue-100 rounded-xl p-4 text-sm text-blue-700">
          <Info size={16} className="mt-0.5 flex-shrink-0" />
          <span>Docker Compose đã bootstrap dữ liệu mẫu. Form trên chỉ cần chạy khi bạn muốn lấy dữ liệu mới từ nguồn thật.</span>
        </div>
      )}

      {/* ── Ingestion Results ── */}
      {pipelineResult && (
        <div className="space-y-4">
          {/* Stat cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="metric-card text-center">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Requested</p>
              <p className="text-3xl font-bold text-slate-800">{pipelineResult.ingestion.requested}</p>
            </div>
            <div className="metric-card text-center">
              <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-2">Passed</p>
              <p className="text-3xl font-bold text-emerald-600">{pipelineResult.ingestion.passed}</p>
            </div>
            <div className="metric-card text-center">
              <p className="text-xs font-semibold text-red-500 uppercase tracking-wide mb-2">Failed</p>
              <p className="text-3xl font-bold text-red-500">{pipelineResult.ingestion.failed}</p>
            </div>
          </div>

          {/* Raw path */}
          <div className="flex items-center gap-2 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Raw path:</span>
            <code className="font-mono">{pipelineResult.ingestion.raw_path}</code>
          </div>

          {/* Details table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="px-5 py-3 bg-slate-50/50 border-b border-slate-100">
              <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Chi tiết ingestion</h3>
            </div>
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header">Ticker</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Message</th>
                </tr>
              </thead>
              <tbody>
                {pipelineResult.ingestion.details.map((d, i) => (
                  <tr key={i} className="table-row">
                    <td className="table-cell font-mono font-semibold text-indigo-700">{d.ticker}</td>
                    <td className="table-cell"><StatusBadge status={d.status} /></td>
                    <td className="table-cell text-slate-400">{d.message || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Preview ── */}
      {ingestedTickers.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Preview dữ liệu</h2>
            <div className="relative w-44">
              <select
                value={previewTicker}
                onChange={(e) => setPreviewTicker(e.target.value)}
                className="input-field appearance-none pr-9 cursor-pointer text-xs h-8"
              >
                {ingestedTickers.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <ChevronDown size={12} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {isLoadingPreview ? (
            <div className="p-6 space-y-2">
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-9 w-full" />)}
            </div>
          ) : previewData.length === 0 ? (
            <div className="flex items-center gap-2 p-5 text-sm text-slate-500">
              <Info size={14} /> Không có dữ liệu cho khoảng thời gian này.
            </div>
          ) : (
            <>
              <table className="w-full">
                <thead>
                  <tr>
                    {['Ngày', 'Đóng cửa', 'Khối lượng', 'MA20', 'RSI 14'].map((h) => (
                      <th key={h} className="table-header">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewData.slice(0, 15).map((p, i) => (
                    <tr key={i} className="table-row">
                      <td className="table-cell font-medium">{format(new Date(p.trading_date), 'dd/MM/yyyy')}</td>
                      <td className="table-cell font-semibold text-slate-800">{p.close_price.toLocaleString('vi-VN')}</td>
                      <td className="table-cell">{p.volume.toLocaleString('vi-VN')}</td>
                      <td className="table-cell text-amber-600">{p.ma20?.toFixed(0) ?? '—'}</td>
                      <td className="table-cell">{p.rsi_14?.toFixed(2) ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400 text-center">
                Hiển thị 15 dòng đầu
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
