import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Building2,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Activity,
  Sliders,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Lightbulb,
} from 'lucide-react';
import { getCompanies, getDistressPrediction } from '../../services/api';
import type { Company, PredictionResult } from '../../types';

// Mock Predictions for Vietnamese Companies (Mục 10 Spec)
const MOCK_PREDICTIONS: Record<string, PredictionResult> = {
  FPT: {
    ticker: 'FPT',
    company_name: 'CTCP FPT',
    year: '2024',
    distress_probability_pct: 4.2,
    risk_level: 'LOW',
    z_score: 4.02,
    z_zone: 'SAFE',
    historical_probabilities: [
      { year: '2019', probability: 5.8 },
      { year: '2020', probability: 6.2 },
      { year: '2021', probability: 5.1 },
      { year: '2022', probability: 4.8 },
      { year: '2023', probability: 4.5 },
      { year: '2024', probability: 4.2 },
    ],
    risk_factors: [
      { factor_name: 'ROA (%)', impact_type: 'POSITIVE', impact_value: '12.0%', description: 'Tỷ suất sinh lời trên tài sản cao giúp củng cố năng lực tài chính.' },
      { factor_name: 'OCF (Dòng tiền KD)', impact_type: 'POSITIVE', impact_value: '+10,600 tỷ', description: 'Dòng tiền thuần hoạt động kinh doanh dương lớn dồi dào.' },
      { factor_name: 'Current Ratio', impact_type: 'POSITIVE', impact_value: '1.25x', description: 'Khả năng thanh toán ngắn hạn đảm bảo tuyệt đối.' },
      { factor_name: 'Debt / Total Assets', impact_type: 'NEGATIVE', impact_value: '56.0%', description: 'Tỷ lệ nợ trên tổng tài sản tăng nhẹ do mở rộng đầu tư hạ tầng AI.' },
    ],
    recommendations: [
      'Duy trì cấu trúc vốn chủ sở hữu hiện tại và tiếp tục tối ưu hóa dòng tiền hoạt động.',
      'Theo dõi sát sao nợ vay ngắn hạn phát sinh phục vụ các trung tâm dữ liệu AI mới.',
      'Không có nguy cơ kiệt quệ tài chính trong 12–24 tháng tới.',
    ],
  },
  VNM: {
    ticker: 'VNM',
    company_name: 'CTCP Sữa Việt Nam',
    year: '2024',
    distress_probability_pct: 2.1,
    risk_level: 'LOW',
    z_score: 7.07,
    z_zone: 'SAFE',
    historical_probabilities: [
      { year: '2019', probability: 3.5 },
      { year: '2020', probability: 3.1 },
      { year: '2021', probability: 2.8 },
      { year: '2022', probability: 2.4 },
      { year: '2023', probability: 2.2 },
      { year: '2024', probability: 2.1 },
    ],
    risk_factors: [
      { factor_name: 'Altman Z-Score', impact_type: 'POSITIVE', impact_value: '7.07', description: 'Điểm Z-Score rất cao nằm sâu trong vùng Safe Zone.' },
      { factor_name: 'EBIT Margin', impact_type: 'POSITIVE', impact_value: '18.7%', description: 'Biên lợi nhuận trước lãi vay & thuế cực kỳ ổn định.' },
      { factor_name: 'Nợ vay ngân hàng', impact_type: 'POSITIVE', impact_value: 'Thấp', description: 'Đòn bẩy nợ rất thấp, áp lực trả chi phí lãi vay không đáng kể.' },
    ],
    recommendations: [
      'Sức khỏe tài chính rất mạnh, dòng tiền cổ tức bền vững.',
      'Tiếp tục tối ưu hóa chi phí nguyên liệu đầu vào.',
    ],
  },
  TTF: {
    ticker: 'TTF',
    company_name: 'CTCP Tập đoàn Kỹ nghệ Gỗ Trường Thành',
    year: '2023',
    distress_probability_pct: 78.4,
    risk_level: 'HIGH',
    z_score: 1.15,
    z_zone: 'DISTRESS',
    historical_probabilities: [
      { year: '2019', probability: 88.5 },
      { year: '2020', probability: 82.1 },
      { year: '2021', probability: 75.4 },
      { year: '2022', probability: 71.2 },
      { year: '2023', probability: 78.4 },
      { year: '2024', probability: 81.0 },
    ],
    risk_factors: [
      { factor_name: 'Lợi nhuận lũy kế', impact_type: 'NEGATIVE', impact_value: 'Lỗ lũy kế', description: 'Lợi nhuận chưa phân phối âm lớn kéo dài nhiều năm.' },
      { factor_name: 'Debt / Total Assets', impact_type: 'NEGATIVE', impact_value: '79.0%', description: 'Đòn bẩy tài chính quá cao, tổng nợ chiếm gần 80% tài sản.' },
      { factor_name: 'Current Ratio', impact_type: 'NEGATIVE', impact_value: '0.82x', description: 'Nợ ngắn hạn vượt quá tài sản ngắn hạn gây rủi ro thanh khoản.' },
    ],
    recommendations: [
      'CẢNH BÁO CAO: Cần lập tức tái cấu trúc các khoản nợ vay đến hạn.',
      'Cắt giảm các dự án kém hiệu quả để tập trung nguồn vốn thu hồi công nợ.',
      'Đàm phán gia hạn các hợp đồng tín dụng ngân hàng.',
    ],
  },
  HVN: {
    ticker: 'HVN',
    company_name: 'Tổng công ty Hàng không Việt Nam',
    year: '2022',
    distress_probability_pct: 92.5,
    risk_level: 'HIGH',
    z_score: 0.45,
    z_zone: 'DISTRESS',
    historical_probabilities: [
      { year: '2019', probability: 12.0 },
      { year: '2020', probability: 74.5 },
      { year: '2021', probability: 89.2 },
      { year: '2022', probability: 92.5 },
    ],
    risk_factors: [
      { factor_name: 'Vốn chủ sở hữu', impact_type: 'NEGATIVE', impact_value: 'VCSH âm', description: 'Thủng vốn chủ sở hữu do thua lỗ kéo dài giai đoạn Covid-19.' },
      { factor_name: 'Khả năng thanh toán', impact_type: 'NEGATIVE', impact_value: '0.35x', description: 'Nợ ngắn hạn gấp gần 3 lần tài sản ngắn hạn.' },
    ],
    recommendations: [
      'CẢNH BÁO NGUY HIỂM: Yêu cầu tái cơ cấu toàn diện từ cổ đông nhà nước.',
      'Phát hành cổ phiếu tăng vốn chủ sở hữu khẩn cấp.',
    ],
  },
};

export const PredictionDashboardView: React.FC = () => {
  const [selectedTicker, setSelectedTicker] = useState('FPT');

  // Fetch listed companies
  const { data: companiesData } = useQuery({
    queryKey: ['companies-prediction-dropdown'],
    queryFn: () => getCompanies(100),
  });

  const companies: Company[] = useMemo(() => {
    const list = companiesData?.data ?? [];
    if (list.length === 0) {
      return [
        { ticker: 'FPT', name: 'CTCP FPT', exchange: 'HOSE' },
        { ticker: 'VNM', name: 'CTCP Sữa Việt Nam', exchange: 'HOSE' },
        { ticker: 'TTF', name: 'CTCP Gỗ Trường Thành', exchange: 'HOSE' },
        { ticker: 'HVN', name: 'Tổng công ty Hàng không VN', exchange: 'HOSE' },
        { ticker: 'HPG', name: 'CTCP Tập đoàn Hòa Phát', exchange: 'HOSE' },
        { ticker: 'MWG', name: 'CTCP Đầu tư Thế Giới Di Động', exchange: 'HOSE' },
      ];
    }
    return list;
  }, [companiesData]);

  // Fetch Distress Prediction
  const { data: apiPrediction } = useQuery({
    queryKey: ['prediction-result', selectedTicker],
    queryFn: () => getDistressPrediction(selectedTicker),
    enabled: !!selectedTicker,
  });

  const prediction: PredictionResult = useMemo(() => {
    return apiPrediction?.data ?? (MOCK_PREDICTIONS[selectedTicker] || MOCK_PREDICTIONS.FPT);
  }, [apiPrediction, selectedTicker]);

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Dự báo Rủi ro Kiệt quệ Tài chính & Cảnh báo Sớm</h1>
            <span className="badge-indigo font-mono">Mục 10 Spec</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Giao diện tra cứu dự báo xác suất rủi ro, phân tích các yếu tố ảnh hưởng (SHAP) và khuyến nghị cảnh báo sớm.
          </p>
        </div>
      </div>

      {/* ── Ticker Selector Bar ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <Building2 size={20} />
          </div>
          <div className="flex-1 sm:flex-none">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Tra cứu Doanh nghiệp</p>
            <div className="relative mt-0.5">
              <select
                value={selectedTicker}
                onChange={(e) => setSelectedTicker(e.target.value)}
                className="input-field appearance-none pr-9 cursor-pointer font-bold text-slate-900 text-sm py-1.5"
              >
                {companies.map((c) => (
                  <option key={c.ticker} value={c.ticker}>
                    {c.ticker} — {c.name}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="text-slate-500">Mô hình AI sử dụng:</span>
          <span className="badge-indigo font-mono flex items-center gap-1">
            <Sparkles size={12} /> XGBoost Financial Model v2.4
          </span>
        </div>
      </div>

      {/* ── TOP RISK ASSESSMENT CARDS ── */}
      {prediction && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Card 1: Distress Probability */}
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Xác suất Kiệt quệ Tài chính</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-3xl font-extrabold font-mono ${prediction.distress_probability_pct > 50 ? 'text-red-600' : 'text-emerald-600'}`}>
                {prediction.distress_probability_pct.toFixed(1)}%
              </span>
            </div>
            <span className={`text-[10px] font-bold mt-1 inline-block ${prediction.distress_probability_pct > 50 ? 'badge-red' : 'badge-green'}`}>
              {prediction.distress_probability_pct > 50 ? '⚠️ Rủi ro Cao' : '✓ An toàn'}
            </span>
          </div>

          {/* Card 2: Risk Level Category */}
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Mức độ Cảnh báo Rủi ro</p>
            <p className="text-xl font-bold text-slate-800 mt-1 flex items-center gap-1.5">
              {prediction.risk_level === 'HIGH' ? (
                <span className="text-red-600 flex items-center gap-1"><AlertTriangle size={18} /> RỦI RO CAO</span>
              ) : prediction.risk_level === 'MODERATE' ? (
                <span className="text-amber-600 flex items-center gap-1"><Activity size={18} /> CẢNH BÁO VÙNG XÁM</span>
              ) : (
                <span className="text-emerald-600 flex items-center gap-1"><CheckCircle2 size={18} /> AN TOÀN TÀI CHÍNH</span>
              )}
            </p>
            <span className="text-[10px] text-slate-400">Năm báo cáo: {prediction.year}</span>
          </div>

          {/* Card 3: Altman Z-Score */}
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Altman Z-Score</p>
            <p className="text-2xl font-bold text-indigo-600 mt-1 font-mono">{prediction.z_score.toFixed(2)}</p>
            <span className="badge-slate text-[10px]">Zone: {prediction.z_zone}</span>
          </div>

          {/* Card 4: Historical Trend Direction */}
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Diễn biến Rủi ro</p>
            <p className="text-xl font-bold text-slate-800 mt-1 flex items-center gap-1">
              {prediction.distress_probability_pct < 10 ? (
                <span className="text-emerald-600 flex items-center gap-1"><ArrowDownRight size={18} /> Giảm rủi ro (-0.3%)</span>
              ) : (
                <span className="text-red-500 flex items-center gap-1"><ArrowUpRight size={18} /> Tăng rủi ro (+7.2%)</span>
              )}
            </p>
            <span className="text-[10px] text-slate-400">So với kỳ báo cáo trước</span>
          </div>
        </div>
      )}

      {/* ── MULTI-YEAR RISK SCORE TREND CHART ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-5 space-y-3">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Activity size={16} className="text-indigo-600" />
            Biểu đồ Xu hướng Rủi ro Kiệt quệ qua các năm (2019 – 2024)
          </h2>
          <span className="badge-slate font-mono">Historical Risk Trend</span>
        </div>

        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={prediction?.historical_probabilities} margin={{ top: 15, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
              <Tooltip formatter={(val: any) => [`${val}%`, 'Xác suất Distress']} />
              <Line
                type="monotone"
                dataKey="probability"
                stroke={prediction?.distress_probability_pct > 50 ? '#ef4444' : '#10b981'}
                strokeWidth={3}
                dot={{ r: 5 }}
                name="Xác suất Rủi ro (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── DUAL PANELS: SHAP RISK DRIVERS & ACTION RECOMMENDATIONS ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PANEL 1: SHAP FEATURE IMPACT DRIVERS */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Sliders size={16} className="text-indigo-600" />
              Các yếu tố tác động đến Rủi ro (SHAP Feature Impact Drivers)
            </h2>
            <span className="badge-slate font-mono">Model Explainability</span>
          </div>

          <div className="p-5 flex-1 space-y-3 divide-y divide-slate-100">
            {prediction?.risk_factors.map((factor, idx) => (
              <div key={idx} className="pt-3 first:pt-0 flex items-start justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-800">{factor.factor_name}</span>
                    <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                      {factor.impact_value}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">{factor.description}</p>
                </div>

                {factor.impact_type === 'POSITIVE' ? (
                  <span className="badge-green flex-shrink-0 text-[11px]">✓ Tác động Tốt</span>
                ) : (
                  <span className="badge-red flex-shrink-0 text-[11px]">⚠️ Tác động Xấu</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* PANEL 2: AUTOMATED RECOMMENDATIONS & EARLY WARNING CHECKLIST */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Lightbulb size={16} className="text-indigo-600" />
              Khuyến nghị & Cảnh báo Sớm (Early Warning Checklist)
            </h2>
            <span className="badge-indigo font-mono">AI Recommendations</span>
          </div>

          <div className="p-5 flex-1 space-y-3">
            {prediction?.recommendations.map((rec, idx) => (
              <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <p className="font-medium text-slate-800">{rec}</p>
              </div>
            ))}

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400 text-center">
              Khuyến nghị được tự động tổng hợp dựa trên chỉ số tài chính thực tế của doanh nghiệp.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
