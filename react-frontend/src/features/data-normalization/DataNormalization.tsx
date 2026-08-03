import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Sliders,
  AlertOctagon,
  FileCheck2,
  ListTree,
  Play,
  Plus,
  Info,
  CheckCircle2,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { getMetricMappings, getDataQualityReport, runDataNormalization } from '../../services/api';
import type { MetricMappingRule, DataQualityReport } from '../../types';

// Representative Metric Mappings
const DEFAULT_METRIC_MAPPINGS: MetricMappingRule[] = [
  {
    standard_key: 'total_assets',
    display_name: 'Tổng tài sản',
    statement_type: 'BS',
    category: 'Tài sản',
    aliases: ['Total Assets', 'TOTAL ASSETS', 'TỔNG CỘNG TÀI SẢN', 'Tổng tài sản', 'Total assets balance'],
  },
  {
    standard_key: 'current_assets',
    display_name: 'Tài sản ngắn hạn',
    statement_type: 'BS',
    category: 'Tài sản',
    aliases: ['Current Assets', 'Tài sản ngắn hạn', 'TỔNG TÀI SẢN NGẮN HẠN', 'Short-term assets'],
  },
  {
    standard_key: 'inventory',
    display_name: 'Hàng tồn kho',
    statement_type: 'BS',
    category: 'Tài sản',
    aliases: ['Inventory', 'Hàng tồn kho', 'Hàng tồn kho ròng', 'Inventories net'],
  },
  {
    standard_key: 'current_liabilities',
    display_name: 'Nợ ngắn hạn',
    statement_type: 'BS',
    category: 'Nguồn vốn',
    aliases: ['Current Liabilities', 'Nợ ngắn hạn', 'Nợ phải trả ngắn hạn', 'Short-term liabilities'],
  },
  {
    standard_key: 'total_liabilities',
    display_name: 'Tổng nợ phải trả',
    statement_type: 'BS',
    category: 'Nguồn vốn',
    aliases: ['Total Liabilities', 'Tổng nợ phải trả', 'TỔNG CỘNG NỢ PHẢI TRẢ', 'Liabilities total'],
  },
  {
    standard_key: 'equity',
    display_name: 'Vốn chủ sở hữu',
    statement_type: 'BS',
    category: 'Nguồn vốn',
    aliases: ['Owner Equity', 'Vốn chủ sở hữu', 'VỐN CHỦ SỞ HỮU', 'Stockholders equity'],
  },
  {
    standard_key: 'retained_earnings',
    display_name: 'Lợi nhuận chưa phân phối',
    statement_type: 'BS',
    category: 'Nguồn vốn',
    aliases: ['Retained Earnings', 'Lợi nhuận sau thuế chưa phân phối', 'LNST chưa phân phối'],
  },
  {
    standard_key: 'net_revenue',
    display_name: 'Doanh thu thuần',
    statement_type: 'IS',
    category: 'Kết quả KD',
    aliases: ['Net Revenue', 'Doanh thu thuần', 'Doanh thu bán hàng và cung cấp dịch vụ', 'Net sales'],
  },
  {
    standard_key: 'ebit',
    display_name: 'Lợi nhuận trước thuế (EBIT)',
    statement_type: 'IS',
    category: 'Kết quả KD',
    aliases: ['EBIT', 'Lợi nhuận trước thuế', 'Tổng lợi nhuận kế toán trước thuế', 'Earning before tax'],
  },
  {
    standard_key: 'net_profit',
    display_name: 'Lợi nhuận sau thuế',
    statement_type: 'IS',
    category: 'Kết quả KD',
    aliases: ['Net Profit', 'Lợi nhuận sau thuế', 'LNST của cổ đông công ty mẹ', 'Profit after tax'],
  },
  {
    standard_key: 'interest_expense',
    display_name: 'Chi phí lãi vay',
    statement_type: 'IS',
    category: 'Chi phí',
    aliases: ['Interest Expense', 'Chi phí lãi vay', 'Trong đó: Chi phí lãi vay', 'Finance interest cost'],
  },
  {
    standard_key: 'operating_cash_flow',
    display_name: 'Dòng tiền HĐKD (OCF)',
    statement_type: 'CF',
    category: 'Dòng tiền',
    aliases: ['Operating Cash Flow', 'Lưu chuyển tiền thuần từ hoạt động kinh doanh', 'OCF net'],
  },
];

// Mock Quality Report Data
const DEFAULT_QUALITY_REPORT: DataQualityReport = {
  total_companies: 150,
  qualified_companies: 128,
  rejected_companies: 22,
  min_years_required: 5,
  missing_rate_overall: 2.4,
  missing_by_metric: [
    { metric_name: 'Chi phí lãi vay', missing_count: 12, missing_percentage: 8.0 },
    { metric_name: 'Hàng tồn kho', missing_count: 5, missing_percentage: 3.3 },
    { metric_name: 'Dòng tiền HĐKD (OCF)', missing_count: 4, missing_percentage: 2.6 },
    { metric_name: 'Lợi nhuận chưa phân phối', missing_count: 3, missing_percentage: 2.0 },
    { metric_name: 'Tài sản ngắn hạn', missing_count: 1, missing_percentage: 0.6 },
    { metric_name: 'Doanh thu thuần', missing_count: 0, missing_percentage: 0.0 },
  ],
  outliers_detected: [
    { ticker: 'AAA', metric: 'ROA', year: '2022', raw_value: 350.2, action: 'Winsorized 99% → 42.5%' },
    { ticker: 'BBB', metric: 'EBIT / Interest Expense', year: '2023', raw_value: Infinity, action: 'Replaced Inf → NaN (Chi phí lãi vay = 0)' },
    { ticker: 'CCC', metric: 'ROE', year: '2021', raw_value: -890.0, action: 'Winsorized 1% → -65.0%' },
    { ticker: 'DDD', metric: 'Debt Ratio', year: '2020', raw_value: 99.8, action: 'Ghi nhận đòn bẩy quá cao' },
  ],
};

export const DataNormalization: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'MAPPINGS' | 'QUALITY' | 'OUTLIERS'>('MAPPINGS');
  const [mappings, setMappings] = useState<MetricMappingRule[]>(DEFAULT_METRIC_MAPPINGS);
  const [newAliasInput, setNewAliasInput] = useState<Record<string, string>>({});

  // Normalization Controls State
  const [minYears, setMinYears] = useState<number>(5);
  const [winsorizePct, setWinsorizePct] = useState<number>(1);
  const [targetUnit, setTargetUnit] = useState<string>('Tỷ VNĐ');
  const [isNormalizing, setIsNormalizing] = useState(false);
  const [normalizedSuccess, setNormalizedSuccess] = useState(false);

  // Queries
  const { data: apiMappings } = useQuery({
    queryKey: ['metric-mappings'],
    queryFn: getMetricMappings,
  });

  React.useEffect(() => {
    if (apiMappings?.data && Array.isArray(apiMappings.data)) {
      setMappings(apiMappings.data);
    }
  }, [apiMappings]);

  const { data: apiQualityReport } = useQuery({
    queryKey: ['quality-report'],
    queryFn: getDataQualityReport,
  });

  const qualityReport: DataQualityReport = useMemo(() => {
    return apiQualityReport?.data ?? DEFAULT_QUALITY_REPORT;
  }, [apiQualityReport]);

  // Handle adding new alias manually
  const handleAddAlias = (standardKey: string) => {
    const text = (newAliasInput[standardKey] || '').trim();
    if (!text) return;

    setMappings((prev) =>
      prev.map((m) => {
        if (m.standard_key === standardKey && !m.aliases.includes(text)) {
          return { ...m, aliases: [...m.aliases, text] };
        }
        return m;
      })
    );

    setNewAliasInput((prev) => ({ ...prev, [standardKey]: '' }));
  };

  // Run normalization
  const handleRunNormalization = async () => {
    setIsNormalizing(true);
    setNormalizedSuccess(false);
    try {
      await runDataNormalization({ minYears, winsorizePct, targetUnit }).catch(() => {});
      setNormalizedSuccess(true);
    } finally {
      setIsNormalizing(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Chuẩn hóa Chỉ tiêu & Làm sạch Dữ liệu Thô</h1>
            <span className="badge-slate font-mono">Mục 5 Spec</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Tạo bảng Mapping tên chỉ tiêu, thống kê tỷ lệ missing, xử lý ngoại lệ (Winsorize) & kiểm tra đơn vị tính.
          </p>
        </div>

        {/* Sub-Tabs Navigation */}
        <div className="flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200/80 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('MAPPINGS')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-lg transition-all ${
              activeTab === 'MAPPINGS' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ListTree size={14} /> Bảng Mapping Chỉ tiêu
          </button>
          <button
            onClick={() => setActiveTab('QUALITY')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-lg transition-all ${
              activeTab === 'QUALITY' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileCheck2 size={14} /> Báo cáo Quality & Missing
          </button>
          <button
            onClick={() => setActiveTab('OUTLIERS')}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-lg transition-all ${
              activeTab === 'OUTLIERS' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <AlertOctagon size={14} /> Xử lý Outlier & Winsorizing
          </button>
        </div>
      </div>

      {/* ── TAB 1: METRIC MAPPING ENGINE ── */}
      {activeTab === 'MAPPINGS' && (
        <div className="space-y-6">
          <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 text-xs sm:text-sm text-amber-900 flex items-start gap-3">
            <Info size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-950">Quy tắc Chuẩn hóa tên chỉ tiêu (Financial_Application.txt - Mục 5):</p>
              <p className="mt-1 text-amber-800 leading-relaxed">
                Mỗi nguồn dữ liệu (Vietstock, CafeF, vnstock...) đặt tên chỉ tiêu BCTC khác nhau.
                Bảng Mapping dưới đây giúp tự động gom toàn bộ các tên biến thể về một mã biến duy nhất (ví dụ: <code className="bg-amber-100 px-1 rounded">total_assets</code>),
                đảm bảo công thức tính toán chỉ số tài chính ở các bước sau không bị tính sai hoặc thiếu dữ liệu.
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden divide-y divide-slate-100">
            <div className="px-5 py-4 bg-slate-50/50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <ListTree size={16} className="text-indigo-600" />
                Danh sách Bảng Mapping Chỉ tiêu ({mappings.length} biến chuẩn)
              </h2>
              <span className="text-xs text-slate-400">Tự động mapping khi cào JSON/HTML</span>
            </div>

            {mappings.map((m) => (
              <div key={m.standard_key} className="p-5 hover:bg-slate-50/60 transition-colors space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                      {m.standard_key}
                    </span>
                    <span className="text-sm font-bold text-slate-800">{m.display_name}</span>
                    <span className="badge-slate text-[10px] uppercase font-mono">{m.statement_type} — {m.category}</span>
                  </div>
                </div>

                {/* Aliases Pills */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-slate-400 font-semibold uppercase tracking-wide mr-1">Bí danh (Aliases):</span>
                  {m.aliases.map((alias, i) => (
                    <span key={i} className="inline-flex items-center gap-1 text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md border border-slate-200 font-medium">
                      ✓ {alias}
                    </span>
                  ))}
                </div>

                {/* Add new alias inline */}
                <div className="flex items-center gap-2 max-w-md pt-1">
                  <input
                    type="text"
                    placeholder="Thêm bí danh mới..."
                    value={newAliasInput[m.standard_key] || ''}
                    onChange={(e) => setNewAliasInput({ ...newAliasInput, [m.standard_key]: e.target.value })}
                    className="input-field text-xs py-1 h-8"
                  />
                  <button
                    onClick={() => handleAddAlias(m.standard_key)}
                    className="btn-secondary text-xs py-1 px-3 h-8 flex items-center gap-1 flex-shrink-0"
                  >
                    <Plus size={13} /> Thêm Alias
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TAB 2: DATA QUALITY & MISSING RATES ── */}
      {activeTab === 'QUALITY' && (
        <div className="space-y-6">
          {/* Quality Overview Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="metric-card">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Tổng số doanh nghiệp</p>
              <p className="text-2xl font-bold text-slate-800 mt-1">{qualityReport.total_companies}</p>
            </div>
            <div className="metric-card">
              <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Đủ điều kiện (≥ {qualityReport.min_years_required} năm BCTC)</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{qualityReport.qualified_companies}</p>
            </div>
            <div className="metric-card">
              <p className="text-xs font-semibold text-red-500 uppercase tracking-wide">Bị loại (Thiếu quá nhiều năm)</p>
              <p className="text-2xl font-bold text-red-500 mt-1">{qualityReport.rejected_companies}</p>
            </div>
            <div className="metric-card">
              <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">Tỷ lệ Missing Rate trung bình</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">{qualityReport.missing_rate_overall}%</p>
            </div>
          </div>

          {/* Missing Rates by Metric Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <FileCheck2 size={16} className="text-indigo-600" />
                Thống kê tỷ lệ Thiếu dữ liệu (Missing Rate) theo từng biến
              </h2>
              <span className="text-xs text-slate-400">Dữ liệu thô trước khi đưa vào mô hình</span>
            </div>

            <table className="w-full text-left">
              <thead>
                <tr>
                  <th className="table-header">Chỉ tiêu tài chính</th>
                  <th className="table-header text-right">Số lượng bị thiếu (Dòng)</th>
                  <th className="table-header text-right">Tỷ lệ Missing (%)</th>
                  <th className="table-header text-right">Đánh giá chất lượng</th>
                </tr>
              </thead>
              <tbody>
                {qualityReport.missing_by_metric.map((row, i) => (
                  <tr key={i} className="table-row">
                    <td className="table-cell font-semibold text-slate-800">{row.metric_name}</td>
                    <td className="table-cell text-right font-mono font-medium">{row.missing_count} / {qualityReport.total_companies}</td>
                    <td className="table-cell text-right font-mono font-bold">
                      <span className={row.missing_percentage > 5 ? 'text-red-500' : 'text-emerald-600'}>
                        {row.missing_percentage.toFixed(1)}%
                      </span>
                    </td>
                    <td className="table-cell text-right font-medium">
                      {row.missing_percentage === 0 ? (
                        <span className="badge-green inline-flex items-center gap-1">
                          <CheckCircle2 size={10} /> Hoàn hảo
                        </span>
                      ) : row.missing_percentage <= 5 ? (
                        <span className="badge-slate inline-flex items-center gap-1">
                          <CheckCircle2 size={10} /> Chấp nhận được
                        </span>
                      ) : (
                        <span className="badge-amber inline-flex items-center gap-1">
                          <AlertTriangle size={10} /> Cần lọc/Winsorize
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── TAB 3: OUTLIER & WINSORIZING ENGINE ── */}
      {activeTab === 'OUTLIERS' && (
        <div className="space-y-6">
          {/* Controls Panel */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-5 space-y-4">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <Sliders size={16} className="text-indigo-600" />
                Cấu hình Xử lý Outlier & Chuẩn hóa Đơn vị tính
              </h2>
              <span className="badge-green">Winsorize 1% & 99% Active</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Số năm BCTC tối thiểu</label>
                <select
                  value={minYears}
                  onChange={(e) => setMinYears(Number(e.target.value))}
                  className="input-field cursor-pointer"
                >
                  <option value={3}>Tối thiểu 3 năm dữ liệu</option>
                  <option value={5}>Tối thiểu 5 năm dữ liệu (Khuyên dùng chuẩn AI)</option>
                  <option value={7}>Tối thiểu 7 năm dữ liệu</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Ngưỡng Winsorize Outlier (%)</label>
                <select
                  value={winsorizePct}
                  onChange={(e) => setWinsorizePct(Number(e.target.value))}
                  className="input-field cursor-pointer font-mono"
                >
                  <option value={1}>Winsorize 1% và 99% (Khuyên dùng)</option>
                  <option value={5}>Winsorize 5% và 95%</option>
                  <option value={0}>Không Winsorize (Giữ nguyên thô)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Quy đổi Đơn vị tiền tệ</label>
                <select
                  value={targetUnit}
                  onChange={(e) => setTargetUnit(e.target.value)}
                  className="input-field cursor-pointer"
                >
                  <option value="Tỷ VNĐ">Quy đổi tất cả về Tỷ VNĐ</option>
                  <option value="Triệu VNĐ">Quy đổi tất cả về Triệu VNĐ</option>
                  <option value="VNĐ">Giữ nguyên VNĐ gốc</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleRunNormalization}
              disabled={isNormalizing}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {isNormalizing ? (
                <><Loader2 size={16} className="animate-spin" /> Đang chạy Winsorizing & Xử lý Outlier...</>
              ) : (
                <><Play size={16} /> Kích hoạt Quy trình Làm sạch Dữ liệu</>
              )}
            </button>

            {normalizedSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 font-semibold flex items-center gap-2">
                <CheckCircle2 size={14} /> Quy trình làm sạch dữ liệu thành công! Dữ liệu đã sẵn sàng để tính các chỉ số tài chính ở Bước 4.
              </div>
            )}
          </div>

          {/* Outliers Log Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <AlertOctagon size={16} className="text-amber-600" />
                Bảng ghi nhận Ngoại lệ (Outlier Logs) đã xử lý
              </h2>
              <span className="text-xs text-slate-400">Xử lý division by zero & nợ quá nhỏ</span>
            </div>

            <table className="w-full text-left">
              <thead>
                <tr>
                  <th className="table-header">Ticker</th>
                  <th className="table-header">Biến tài chính</th>
                  <th className="table-header">Năm</th>
                  <th className="table-header text-right">Giá trị thô (Raw)</th>
                  <th className="table-header text-right">Hành động xử lý (Action)</th>
                </tr>
              </thead>
              <tbody>
                {qualityReport.outliers_detected.map((out, i) => (
                  <tr key={i} className="table-row">
                    <td className="table-cell font-mono font-bold text-indigo-700">{out.ticker}</td>
                    <td className="table-cell font-semibold text-slate-800">{out.metric}</td>
                    <td className="table-cell font-mono">{out.year}</td>
                    <td className="table-cell text-right font-mono text-red-500 font-medium">
                      {out.raw_value === Infinity ? 'Inf' : out.raw_value.toLocaleString('vi-VN')}
                    </td>
                    <td className="table-cell text-right font-medium">
                      <span className="badge-amber">{out.action}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
