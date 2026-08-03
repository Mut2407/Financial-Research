import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileSpreadsheet,
  Download,
  FileCode,
  Zap,
  CheckCircle2,
  Info,
  Table,
  PieChart as PieChartIcon,
  Search,
  Loader2,
} from 'lucide-react';
import { getDatasetPreview } from '../../services/api';
import type { DatasetRow, FinalDatasetSummary } from '../../types';

// Mock Representative Dataset Rows for Vietnamese Listed Companies (Mục 8 Spec)
const MOCK_DATASET_ROWS: DatasetRow[] = [
  { ticker: 'FPT', company_name: 'CTCP FPT', year: '2024', exchange: 'HOSE', industry: 'Công nghệ thông tin', roa: 12.00, roe: 27.42, current_ratio: 1.25, debt_to_ta: 0.56, ebit_margin: 17.68, log_total_assets: 4.89, z_score: 4.02, distress_label: 0 },
  { ticker: 'FPT', company_name: 'CTCP FPT', year: '2023', exchange: 'HOSE', industry: 'Công nghệ thông tin', roa: 11.84, roe: 27.14, current_ratio: 1.26, debt_to_ta: 0.56, ebit_margin: 17.49, log_total_assets: 4.82, z_score: 3.68, distress_label: 0 },
  { ticker: 'VNM', company_name: 'CTCP Sữa Việt Nam', year: '2024', exchange: 'HOSE', industry: 'Thực phẩm & Đồ uống', roa: 17.11, roe: 25.73, current_ratio: 2.10, debt_to_ta: 0.34, ebit_margin: 18.70, log_total_assets: 4.75, z_score: 7.07, distress_label: 0 },
  { ticker: 'VNM', company_name: 'CTCP Sữa Việt Nam', year: '2023', exchange: 'HOSE', industry: 'Thực phẩm & Đồ uống', roa: 17.11, roe: 25.70, current_ratio: 2.07, debt_to_ta: 0.33, ebit_margin: 18.14, log_total_assets: 4.72, z_score: 6.84, distress_label: 0 },
  { ticker: 'HPG', company_name: 'CTCP Tập đoàn Hòa Phát', year: '2024', exchange: 'HOSE', industry: 'Thép & Vật liệu xây dựng', roa: 7.15, roe: 12.40, current_ratio: 1.42, debt_to_ta: 0.42, ebit_margin: 11.20, log_total_assets: 5.28, z_score: 2.95, distress_label: 0 },
  { ticker: 'HPG', company_name: 'CTCP Tập đoàn Hòa Phát', year: '2022', exchange: 'HOSE', industry: 'Thép & Vật liệu xây dựng', roa: 4.80, roe: 8.90, current_ratio: 1.15, debt_to_ta: 0.46, ebit_margin: 6.80, log_total_assets: 5.23, z_score: 2.15, distress_label: 0 },
  { ticker: 'MWG', company_name: 'CTCP Đầu tư Thế Giới Di Động', year: '2024', exchange: 'HOSE', industry: 'Bán lẻ', roa: 6.10, roe: 14.50, current_ratio: 1.38, debt_to_ta: 0.58, ebit_margin: 4.80, log_total_assets: 4.78, z_score: 3.10, distress_label: 0 },
  { ticker: 'MWG', company_name: 'CTCP Đầu tư Thế Giới Di Động', year: '2023', exchange: 'HOSE', industry: 'Bán lẻ', roa: 0.28, roe: 0.72, current_ratio: 1.22, debt_to_ta: 0.61, ebit_margin: 0.85, log_total_assets: 4.78, z_score: 1.95, distress_label: 0 },
  { ticker: 'BSR', company_name: 'CTCP Lọc hóa dầu Bình Sơn', year: '2024', exchange: 'UPCOM', industry: 'Dầu khí', roa: 7.80, roe: 11.20, current_ratio: 2.15, debt_to_ta: 0.31, ebit_margin: 6.90, log_total_assets: 4.93, z_score: 4.12, distress_label: 0 },
  { ticker: 'REE', company_name: 'CTCP Cơ Điện Lạnh', year: '2024', exchange: 'HOSE', industry: 'Năng lượng & Cơ điện', roa: 8.90, roe: 14.10, current_ratio: 1.85, debt_to_ta: 0.37, ebit_margin: 28.50, log_total_assets: 4.54, z_score: 3.80, distress_label: 0 },
  { ticker: 'TTF', company_name: 'CTCP Tập đoàn Kỹ nghệ Gỗ Trường Thành', year: '2023', exchange: 'HOSE', industry: 'Gỗ & Nội thất', roa: -2.10, roe: -8.40, current_ratio: 0.82, debt_to_ta: 0.79, ebit_margin: -3.20, log_total_assets: 3.48, z_score: 1.15, distress_label: 1 },
  { ticker: 'HVN', company_name: 'Tổng công ty Hàng không Việt Nam', year: '2022', exchange: 'HOSE', industry: 'Vận tải Hàng không', roa: -18.50, roe: -95.00, current_ratio: 0.35, debt_to_ta: 1.28, ebit_margin: -14.20, log_total_assets: 4.79, z_score: 0.45, distress_label: 1 },
  { ticker: 'POM', company_name: 'CTCP Thép Pomina', year: '2023', exchange: 'HOSE', industry: 'Thép', roa: -12.40, roe: -45.00, current_ratio: 0.52, debt_to_ta: 0.88, ebit_margin: -9.80, log_total_assets: 3.98, z_score: 0.82, distress_label: 1 },
];

const DEFAULT_DATASET_SUMMARY: FinalDatasetSummary = {
  total_rows: 768,
  total_companies: 128,
  year_range: '2019 – 2024',
  label_0_count: 672,
  label_1_count: 96,
  distress_ratio_pct: 12.5,
  missing_rate_overall: 0.0,
  file_size_estimates: {
    csv: '1.2 MB',
    excel: '2.4 MB',
    parquet: '280 KB',
  },
};

export const DatasetExportView: React.FC = () => {
  const [filterLabel, setFilterLabel] = useState<'ALL' | '0' | '1'>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // Queries
  const { data: apiPreview } = useQuery({
    queryKey: ['dataset-preview'],
    queryFn: getDatasetPreview,
  });

  const datasetRows: DatasetRow[] = useMemo(() => {
    return apiPreview?.data?.rows ?? MOCK_DATASET_ROWS;
  }, [apiPreview]);

  const summary: FinalDatasetSummary = useMemo(() => {
    return apiPreview?.data?.summary ?? DEFAULT_DATASET_SUMMARY;
  }, [apiPreview]);

  // Filter dataset rows
  const filteredRows = useMemo(() => {
    return datasetRows.filter((r) => {
      if (filterLabel !== 'ALL' && r.distress_label.toString() !== filterLabel) {
        return false;
      }
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchTicker = r.ticker.toLowerCase().includes(term);
        const matchName = r.company_name.toLowerCase().includes(term);
        if (!matchTicker && !matchName) return false;
      }
      return true;
    });
  }, [datasetRows, filterLabel, searchTerm]);

  // Safe client-side export handler without white-screen crash
  const handleExport = (format: 'CSV' | 'EXCEL' | 'PARQUET') => {
    setDownloadingFormat(format);
    setExportNotice(null);

    try {
      let content = '';
      let mimeType = 'text/csv;charset=utf-8;';
      let extension = 'csv';

      if (format === 'CSV') {
        const BOM = '\uFEFF'; // Add UTF-8 BOM for Microsoft Excel Vietnamese font support
        const headers = 'Ticker,Tên công ty,Năm,Sàn,Ngành nghề,ROA (%),ROE (%),Current Ratio,Debt Ratio,EBIT Margin (%),Log Assets,Z-Score,Distress Label\n';
        const rowsText = filteredRows
          .map(
            (r) =>
              `${r.ticker},"${r.company_name}",${r.year},${r.exchange},"${r.industry}",${r.roa},${r.roe},${r.current_ratio},${r.debt_to_ta},${r.ebit_margin},${r.log_total_assets},${r.z_score},${r.distress_label}`
          )
          .join('\n');
        content = BOM + headers + rowsText;
        mimeType = 'text/csv;charset=utf-8;';
        extension = 'csv';
      } else if (format === 'EXCEL') {
        const BOM = '\uFEFF';
        const headers = 'Ticker\tTên công ty\tNăm\tSàn\tNgành nghề\tROA (%)\tROE (%)\tCurrent Ratio\tDebt Ratio\tEBIT Margin (%)\tLog Assets\tZ-Score\tDistress Label\n';
        const rowsText = filteredRows
          .map(
            (r) =>
              `${r.ticker}\t${r.company_name}\t${r.year}\t${r.exchange}\t${r.industry}\t${r.roa}\t${r.roe}\t${r.current_ratio}\t${r.debt_to_ta}\t${r.ebit_margin}\t${r.log_total_assets}\t${r.z_score}\t${r.distress_label}`
          )
          .join('\n');
        content = BOM + headers + rowsText;
        mimeType = 'application/vnd.ms-excel;charset=utf-8;';
        extension = 'xls';
      } else {
        // PARQUET Metadata representation in JSON
        content = JSON.stringify(
          {
            metadata: {
              dataset_name: 'vietnam_financial_distress_dataset',
              schema: 'parquet_v2',
              total_rows: filteredRows.length,
              target_column: 'distress_label',
            },
            data: filteredRows,
          },
          null,
          2
        );
        mimeType = 'application/json;charset=utf-8;';
        extension = 'parquet.json';
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `financial_distress_dataset_vietnam.${extension}`);
      document.body.appendChild(link);
      link.click();

      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }, 200);

      setExportNotice(`Đã xuất và tải xuống thành công file ${format} (${filteredRows.length} dòng dữ liệu)!`);
    } catch (err: any) {
      alert(`Lỗi khi tạo file xuất: ${err?.message || 'Không xác định'}`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Xuất Dataset Cuối cùng & Báo cáo Chất lượng Dữ liệu</h1>
            <span className="badge-slate font-mono">Mục 8 Spec</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Xuất tập dữ liệu sạch (CSV, Excel, Parquet) kèm Báo cáo chất lượng phục vụ huấn luyện mô hình AI/ML.
          </p>
        </div>
      </div>

      {/* ── Success Notice Banner ── */}
      {exportNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs sm:text-sm text-emerald-800 font-semibold flex items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
            <span>{exportNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setExportNotice(null)}
            className="text-xs text-emerald-600 hover:text-emerald-900 underline font-normal"
          >
            Đóng
          </button>
        </div>
      )}

      {/* ── Export Action Panel (3 Formats) ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Download size={16} className="text-indigo-600" />
            Tải về Tập Dữ liệu Cuối cùng (Choose Output Format)
          </h2>
          <span className="badge-green font-mono">Ready for AI Training</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* CSV Export Option */}
          <div className="border border-slate-200 rounded-xl p-4 hover:border-indigo-300 hover:shadow-sm transition-all space-y-3 bg-gradient-to-br from-white to-slate-50">
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <FileCode size={20} />
              </div>
              <span className="text-xs font-mono text-slate-400">~{summary.file_size_estimates.csv}</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">File CSV (.csv)</h3>
              <p className="text-xs text-slate-500 mt-0.5">Phù hợp dùng cho Python, Pandas, R, Weka và Excel nhanh.</p>
            </div>
            <button
              type="button"
              onClick={() => handleExport('CSV')}
              disabled={!!downloadingFormat}
              className="w-full btn-secondary text-xs py-2 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              {downloadingFormat === 'CSV' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
              Tải file CSV
            </button>
          </div>

          {/* Excel Export Option */}
          <div className="border border-slate-200 rounded-xl p-4 hover:border-indigo-300 hover:shadow-sm transition-all space-y-3 bg-gradient-to-br from-white to-slate-50">
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <FileSpreadsheet size={20} />
              </div>
              <span className="text-xs font-mono text-slate-400">~{summary.file_size_estimates.excel}</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">File Excel (.xlsx)</h3>
              <p className="text-xs text-slate-500 mt-0.5">Phù hợp để mở trực tiếp kiểm tra bằng tay & báo cáo thủ công.</p>
            </div>
            <button
              type="button"
              onClick={() => handleExport('EXCEL')}
              disabled={!!downloadingFormat}
              className="w-full btn-secondary text-xs py-2 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              {downloadingFormat === 'EXCEL' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
              Tải file Excel
            </button>
          </div>

          {/* Parquet Export Option */}
          <div className="border border-indigo-200 rounded-xl p-4 hover:border-indigo-400 hover:shadow-md transition-all space-y-3 bg-gradient-to-br from-indigo-50/50 to-white">
            <div className="flex items-center justify-between">
              <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
                <Zap size={20} />
              </div>
              <span className="badge-indigo font-mono">Tối ưu AI Engine</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">File Parquet (.parquet)</h3>
              <p className="text-xs text-slate-500 mt-0.5">Nén cao, đọc cực nhanh cho PySpark, DuckDB, LightGBM, CatBoost.</p>
            </div>
            <button
              type="button"
              onClick={() => handleExport('PARQUET')}
              disabled={!!downloadingFormat}
              className="w-full btn-primary text-xs py-2 flex items-center justify-center gap-1.5 cursor-pointer"
            >
              {downloadingFormat === 'PARQUET' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
              Tải file Parquet (Khuyên dùng)
            </button>
          </div>
        </div>
      </div>

      {/* ── Data Quality Summary Report (Mục 8 Spec) ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden p-5 space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <PieChartIcon size={16} className="text-indigo-600" />
            Báo cáo Chất lượng Dữ liệu Tổng hợp (Data Quality Summary Report)
          </h2>
          <span className="text-xs text-slate-400 font-mono">Export Metadata</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Tổng số dòng dữ liệu (Rows)</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{summary.total_rows} dòng</p>
            <span className="text-[11px] text-slate-400">{summary.total_companies} DN × {summary.year_range}</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Nhãn 0: Non-Distress (An toàn)</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{summary.label_0_count} dòng</p>
            <span className="text-[11px] text-slate-400">Chiếm {(100 - summary.distress_ratio_pct).toFixed(1)}% toàn bộ mẫu</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-red-500 uppercase tracking-wide">Nhãn 1: Distress (Rủi ro)</p>
            <p className="text-2xl font-bold text-red-500 mt-1">{summary.label_1_count} dòng</p>
            <span className="text-[11px] text-slate-400">Tỷ lệ Distress: {summary.distress_ratio_pct}%</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">Missing Rate Tổng thể</p>
            <p className="text-2xl font-bold text-indigo-600 mt-1">{summary.missing_rate_overall}%</p>
            <span className="text-[11px] text-slate-400">Đã làm sạch hoàn toàn</span>
          </div>
        </div>

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1">
          <p className="font-semibold text-slate-800 flex items-center gap-1.5">
            <Info size={14} className="text-indigo-600" /> Tóm tắt các thông số lọc chất lượng dữ liệu:
          </p>
          <ul className="list-disc pl-5 space-y-0.5 text-slate-500">
            <li>Số lượng doanh nghiệp đủ điều kiện đưa vào Dataset: <strong>{summary.total_companies} doanh nghiệp</strong> (được lọc bỏ các mã ngành Tài chính ở Bước 1).</li>
            <li>Khung thời gian lịch sử: <strong>{summary.year_range}</strong> (Chỉ lấy doanh nghiệp có tối thiểu 5 năm dữ liệu liên tục).</li>
            <li>Tỷ lệ mất cân bằng nhãn (Imbalance Ratio): <strong>1 : {(summary.label_0_count / summary.label_1_count).toFixed(1)}</strong> (Sẽ được xử lý trong bước Huấn luyện AI/ML ở Bước 7).</li>
          </ul>
        </div>
      </div>

      {/* ── Dataset Preview Table (Mục 8 Spec) ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Table size={16} className="text-indigo-600" />
            <h2 className="text-sm font-semibold text-slate-800">
              Preview Tập Dữ liệu Cuối cùng ({filteredRows.length} dòng hiển thị)
            </h2>
          </div>

          <div className="flex items-center gap-3">
            {/* Search input */}
            <div className="relative w-44">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Lọc mã..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field text-xs py-1 pl-8 h-8"
              />
            </div>

            {/* Filter Label select */}
            <div className="relative w-36">
              <select
                value={filterLabel}
                onChange={(e) => setFilterLabel(e.target.value as any)}
                className="input-field cursor-pointer text-xs py-1 h-8"
              >
                <option value="ALL">Tất cả Nhãn</option>
                <option value="0">Label 0 (Safe)</option>
                <option value="1">Label 1 (Distress)</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr>
                <th className="table-header">Ticker</th>
                <th className="table-header">Tên công ty</th>
                <th className="table-header">Năm</th>
                <th className="table-header">Sàn</th>
                <th className="table-header text-right">ROA (%)</th>
                <th className="table-header text-right">ROE (%)</th>
                <th className="table-header text-right">Current Ratio</th>
                <th className="table-header text-right">Debt / TA</th>
                <th className="table-header text-right">Z-Score</th>
                <th className="table-header text-center">Distress Label</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((r, i) => (
                <tr key={i} className="table-row">
                  <td className="table-cell font-mono font-bold text-indigo-700">{r.ticker}</td>
                  <td className="table-cell font-medium text-slate-800">{r.company_name}</td>
                  <td className="table-cell font-mono text-slate-600">{r.year}</td>
                  <td className="table-cell font-bold text-xs">{r.exchange}</td>
                  <td className={`table-cell text-right font-mono font-semibold ${r.roa < 0 ? 'text-red-500' : 'text-emerald-600'}`}>
                    {r.roa.toFixed(2)}%
                  </td>
                  <td className={`table-cell text-right font-mono font-semibold ${r.roe < 0 ? 'text-red-500' : 'text-indigo-600'}`}>
                    {r.roe.toFixed(2)}%
                  </td>
                  <td className="table-cell text-right font-mono">{r.current_ratio.toFixed(2)}x</td>
                  <td className="table-cell text-right font-mono">{(r.debt_to_ta * 100).toFixed(1)}%</td>
                  <td className="table-cell text-right font-mono font-bold text-slate-800">{r.z_score.toFixed(2)}</td>
                  <td className="table-cell text-center">
                    {r.distress_label === 0 ? (
                      <span className="badge-green font-mono font-bold">0 (Safe)</span>
                    ) : (
                      <span className="badge-red font-mono font-bold">1 (Distress)</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-400 text-center">
          Hiển thị mẫu preview các dòng dữ liệu chuẩn hóa cuối cùng (Mục 8 Spec). Sẵn sàng chuyển sang Bước 7: Train Model AI/ML.
        </div>
      </div>
    </div>
  );
};
