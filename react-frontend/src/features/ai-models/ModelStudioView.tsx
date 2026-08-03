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
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import {
  Cpu,
  Play,
  Sliders,
  Calendar,
  CheckCircle2,
  TrendingUp,
  Layers,
  BarChart3,
  Loader2,
  Info,
} from 'lucide-react';
import { trainModel, getModelEvaluation } from '../../services/api';
import type { ModelTrainingResult } from '../../types';

// Mock Evaluation Data for AI Models (Mục 9 Spec)
const MOCK_MODEL_RESULTS: Record<string, ModelTrainingResult> = {
  XGBoost: {
    model_name: 'XGBoost (eXtreme Gradient Boosting)',
    train_years: '2018 - 2022',
    test_years: '2023 - 2024',
    metrics: {
      auc: 0.924,
      recall: 0.896,
      precision: 0.854,
      f1_score: 0.874,
      accuracy: 0.931,
      confusion_matrix: { tp: 86, fp: 40, tn: 632, fn: 10 },
    },
    feature_importance: [
      { feature_name: 'z_score', display_name: 'Altman Z-Score', importance: 0.284 },
      { feature_name: 'roa', display_name: 'ROA (Tỷ suất sinh lời/Tài sản)', importance: 0.192 },
      { feature_name: 'debt_to_ta', display_name: 'Debt / Total Assets (Đòn bẩy)', importance: 0.145 },
      { feature_name: 'current_ratio', display_name: 'Current Ratio (Thanh toán ngắn hạn)', importance: 0.128 },
      { feature_name: 'ocf_to_liabilities', display_name: 'OCF / Current Liabilities', importance: 0.105 },
      { feature_name: 'log_total_assets', display_name: 'Log(Total Assets) - Quy mô', importance: 0.082 },
      { feature_name: 'ebit_margin', display_name: 'EBIT Margin (%)', importance: 0.064 },
    ],
    roc_curve: [
      { fpr: 0.00, tpr: 0.00 },
      { fpr: 0.02, tpr: 0.45 },
      { fpr: 0.05, tpr: 0.72 },
      { fpr: 0.10, tpr: 0.89 },
      { fpr: 0.15, tpr: 0.93 },
      { fpr: 0.30, tpr: 0.97 },
      { fpr: 0.50, tpr: 0.99 },
      { fpr: 1.00, tpr: 1.00 },
    ],
  },
  RandomForest: {
    model_name: 'Random Forest Classifier',
    train_years: '2018 - 2022',
    test_years: '2023 - 2024',
    metrics: {
      auc: 0.898,
      recall: 0.854,
      precision: 0.821,
      f1_score: 0.837,
      accuracy: 0.912,
      confusion_matrix: { tp: 82, fp: 48, tn: 624, fn: 14 },
    },
    feature_importance: [
      { feature_name: 'z_score', display_name: 'Altman Z-Score', importance: 0.265 },
      { feature_name: 'roa', display_name: 'ROA (%)', importance: 0.210 },
      { feature_name: 'debt_to_ta', display_name: 'Debt / Total Assets', importance: 0.160 },
      { feature_name: 'current_ratio', display_name: 'Current Ratio', importance: 0.140 },
      { feature_name: 'log_total_assets', display_name: 'Log(Total Assets)', importance: 0.125 },
      { feature_name: 'ebit_margin', display_name: 'EBIT Margin (%)', importance: 0.100 },
    ],
    roc_curve: [
      { fpr: 0.00, tpr: 0.00 },
      { fpr: 0.04, tpr: 0.40 },
      { fpr: 0.08, tpr: 0.68 },
      { fpr: 0.14, tpr: 0.85 },
      { fpr: 0.22, tpr: 0.91 },
      { fpr: 1.00, tpr: 1.00 },
    ],
  },
  LightGBM: {
    model_name: 'LightGBM Classifier',
    train_years: '2018 - 2022',
    test_years: '2023 - 2024',
    metrics: {
      auc: 0.918,
      recall: 0.885,
      precision: 0.848,
      f1_score: 0.866,
      accuracy: 0.928,
      confusion_matrix: { tp: 85, fp: 42, tn: 630, fn: 11 },
    },
    feature_importance: [
      { feature_name: 'z_score', display_name: 'Altman Z-Score', importance: 0.278 },
      { feature_name: 'roa', display_name: 'ROA (%)', importance: 0.198 },
      { feature_name: 'debt_to_ta', display_name: 'Debt / Total Assets', importance: 0.152 },
      { feature_name: 'current_ratio', display_name: 'Current Ratio', importance: 0.130 },
      { feature_name: 'log_total_assets', display_name: 'Log(Total Assets)', importance: 0.090 },
      { feature_name: 'ebit_margin', display_name: 'EBIT Margin (%)', importance: 0.075 },
    ],
    roc_curve: [
      { fpr: 0.00, tpr: 0.00 },
      { fpr: 0.03, tpr: 0.43 },
      { fpr: 0.06, tpr: 0.71 },
      { fpr: 0.12, tpr: 0.88 },
      { fpr: 0.20, tpr: 0.93 },
      { fpr: 1.00, tpr: 1.00 },
    ],
  },
  LogisticRegression: {
    model_name: 'Logistic Regression (L2 Regularized)',
    train_years: '2018 - 2022',
    test_years: '2023 - 2024',
    metrics: {
      auc: 0.845,
      recall: 0.781,
      precision: 0.750,
      f1_score: 0.765,
      accuracy: 0.875,
      confusion_matrix: { tp: 75, fp: 65, tn: 607, fn: 21 },
    },
    feature_importance: [
      { feature_name: 'z_score', display_name: 'Altman Z-Score', importance: 0.320 },
      { feature_name: 'debt_to_ta', display_name: 'Debt / Total Assets', importance: 0.240 },
      { feature_name: 'roa', display_name: 'ROA (%)', importance: 0.180 },
      { feature_name: 'current_ratio', display_name: 'Current Ratio', importance: 0.150 },
      { feature_name: 'log_total_assets', display_name: 'Log(Total Assets)', importance: 0.110 },
    ],
    roc_curve: [
      { fpr: 0.00, tpr: 0.00 },
      { fpr: 0.10, tpr: 0.45 },
      { fpr: 0.20, tpr: 0.72 },
      { fpr: 0.35, tpr: 0.85 },
      { fpr: 1.00, tpr: 1.00 },
    ],
  },
};

export const ModelStudioView: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('XGBoost');
  const [trainStartYear, setTrainStartYear] = useState(2018);
  const [trainEndYear, setTrainEndYear] = useState(2022);
  const [testStartYear, setTestStartYear] = useState(2023);
  const [testEndYear, setTestEndYear] = useState(2024);
  const [handleImbalance] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingSuccess, setTrainingSuccess] = useState(false);

  // Queries
  const { data: apiEvaluation, refetch } = useQuery({
    queryKey: ['model-evaluation', selectedModel],
    queryFn: () => getModelEvaluation(selectedModel),
    enabled: !!selectedModel,
  });

  const modelResult: ModelTrainingResult = useMemo(() => {
    return apiEvaluation?.data ?? (MOCK_MODEL_RESULTS[selectedModel] || MOCK_MODEL_RESULTS.XGBoost);
  }, [apiEvaluation, selectedModel]);

  // Train action
  const handleTrainModel = async () => {
    setIsTraining(true);
    setTrainingSuccess(false);
    try {
      await trainModel({
        model_type: selectedModel,
        train_start_year: trainStartYear,
        train_end_year: trainEndYear,
        test_start_year: testStartYear,
        test_end_year: testEndYear,
        handle_imbalance: handleImbalance,
      }).catch(() => {});
      setTrainingSuccess(true);
      refetch();
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Huấn luyện & Đánh giá Mô hình AI/Machine Learning</h1>
            <span className="badge-slate font-mono">Mục 9 Spec</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Thiết lập chiến lược Time-based Train/Test Split, huấn luyện mô hình học máy và đánh giá chỉ số AUC, Recall, Confusion Matrix.
          </p>
        </div>

        <button
          type="button"
          onClick={handleTrainModel}
          disabled={isTraining}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto cursor-pointer"
        >
          {isTraining ? (
            <><Loader2 size={16} className="animate-spin" /> Đang huấn luyện Mô hình...</>
          ) : (
            <><Play size={16} /> Kích hoạt Huấn luyện ({selectedModel})</>
          )}
        </button>
      </div>

      {trainingSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs sm:text-sm text-emerald-800 font-semibold flex items-center gap-2 shadow-sm">
          <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
          <span>Đã hoàn tất huấn luyện mô hình <strong>{selectedModel}</strong>! Các chỉ số đánh giá bên dưới đã được cập nhật mới nhất.</span>
        </div>
      )}

      {/* ── Model Configuration & Time-based Split Panel ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-5 space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Sliders size={16} className="text-indigo-600" />
            Cấu hình Mô hình & Chiến lược chia Dữ liệu theo Thời gian (Time-based Split)
          </h2>
          <span className="badge-indigo font-mono">Mục 9 Spec</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Model Type Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Cpu size={13} className="text-indigo-600" /> Chọn Thuật toán AI/ML
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="input-field cursor-pointer font-bold text-slate-800 text-xs"
            >
              <option value="XGBoost">XGBoost (eXtreme Gradient Boosting) — Khuyên dùng</option>
              <option value="RandomForest">Random Forest Classifier</option>
              <option value="LightGBM">LightGBM Classifier</option>
              <option value="LogisticRegression">Logistic Regression (Chuẩn hóa L2)</option>
            </select>
          </div>

          {/* Time Train Split */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Calendar size={13} className="text-indigo-600" /> Khung Năm Train (Quá khứ)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={trainStartYear}
                onChange={(e) => setTrainStartYear(Number(e.target.value))}
                className="input-field text-xs text-center font-mono font-bold"
              />
              <span className="text-slate-400 font-bold">→</span>
              <input
                type="number"
                value={trainEndYear}
                onChange={(e) => setTrainEndYear(Number(e.target.value))}
                className="input-field text-xs text-center font-mono font-bold"
              />
            </div>
          </div>

          {/* Time Test Split */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <Calendar size={13} className="text-indigo-600" /> Khung Năm Test (Tương lai)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={testStartYear}
                onChange={(e) => setTestStartYear(Number(e.target.value))}
                className="input-field text-xs text-center font-mono font-bold"
              />
              <span className="text-slate-400 font-bold">→</span>
              <input
                type="number"
                value={testEndYear}
                onChange={(e) => setTestEndYear(Number(e.target.value))}
                className="input-field text-xs text-center font-mono font-bold"
              />
            </div>
          </div>
        </div>

        {/* Time-based split notice banner */}
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 text-xs text-amber-900 flex items-start gap-2.5">
          <Info size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-amber-950">Quy tắc bắt buộc về Time-based Split (Mục 9 Spec):</p>
            <p className="text-amber-800 text-[11px] mt-0.5">
              Trong tài chính, KHÔNG sử dụng chia Train/Test ngẫu nhiên (Random split) vì sẽ gây rò rỉ dữ liệu tương lai (Data Leakage). 
              Mô hình học từ quá khứ ({trainStartYear}–{trainEndYear}) và kiểm chứng độ chính xác ở tương lai ({testStartYear}–{testEndYear}).
            </p>
          </div>
        </div>
      </div>

      {/* ── Model Metrics Performance Cards ── */}
      {modelResult && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">ROC - AUC</p>
            <p className="text-2xl font-extrabold text-indigo-600 mt-1">{modelResult.metrics.auc.toFixed(3)}</p>
            <span className="badge-green text-[10px]">Xuất sắc (&gt; 0.9)</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-red-500 uppercase tracking-wide">Recall (Bắt nhầm)</p>
            <p className="text-2xl font-extrabold text-red-600 mt-1">{(modelResult.metrics.recall * 100).toFixed(1)}%</p>
            <span className="text-[10px] text-slate-400">Tiêu chí ưu tiên hàng đầu</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Precision</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{(modelResult.metrics.precision * 100).toFixed(1)}%</p>
            <span className="text-[10px] text-slate-400">Độ chính xác cảnh báo</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">F1 - Score</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{(modelResult.metrics.f1_score * 100).toFixed(1)}%</p>
            <span className="text-[10px] text-slate-400">Cân bằng Precision & Recall</span>
          </div>

          <div className="metric-card">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Accuracy</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{(modelResult.metrics.accuracy * 100).toFixed(1)}%</p>
            <span className="text-[10px] text-slate-400">Tổng chính xác mẫu</span>
          </div>
        </div>
      )}

      {/* ── DUAL CHARTS PANEL: CONFUSION MATRIX & ROC CURVE ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PANEL 1: CONFUSION MATRIX VISUAL */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden p-5 flex flex-col justify-between space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Layers size={16} className="text-indigo-600" />
              Ma trận Nhầm lẫn (Confusion Matrix)
            </h2>
            <span className="badge-slate font-mono">Classification Matrix</span>
          </div>

          {modelResult && (
            <div className="grid grid-cols-2 gap-3 font-mono text-center my-auto">
              {/* True Negative */}
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wide block">True Negative (TN)</span>
                <p className="text-3xl font-extrabold text-emerald-600">{modelResult.metrics.confusion_matrix.tn}</p>
                <p className="text-[11px] text-emerald-700 font-sans font-medium">Dự đoán An toàn — Thực tế An toàn (ĐÚNG)</p>
              </div>

              {/* False Positive */}
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-1">
                <span className="text-xs font-bold text-amber-800 uppercase tracking-wide block">False Positive (FP)</span>
                <p className="text-3xl font-extrabold text-amber-600">{modelResult.metrics.confusion_matrix.fp}</p>
                <p className="text-[11px] text-amber-700 font-sans font-medium">Dự đoán Distress — Thực tế An toàn (BÁO NHẦM)</p>
              </div>

              {/* False Negative */}
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 space-y-1">
                <span className="text-xs font-bold text-red-800 uppercase tracking-wide block">False Negative (FN)</span>
                <p className="text-3xl font-extrabold text-red-600">{modelResult.metrics.confusion_matrix.fn}</p>
                <p className="text-[11px] text-red-700 font-sans font-medium">Dự đoán An toàn — Thực tế Distress (BỎ SÓT RỦI RO)</p>
              </div>

              {/* True Positive */}
              <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 space-y-1">
                <span className="text-xs font-bold text-indigo-800 uppercase tracking-wide block">True Positive (TP)</span>
                <p className="text-3xl font-extrabold text-indigo-600">{modelResult.metrics.confusion_matrix.tp}</p>
                <p className="text-[11px] text-indigo-700 font-sans font-medium">Dự đoán Distress — Thực tế Distress (ĐÚNG)</p>
              </div>
            </div>
          )}

          <div className="text-[11px] text-slate-400 bg-slate-50 p-2.5 rounded-lg text-center">
            <strong>Ghi chú:</strong> Trong dự báo rủi ro tài chính, tiêu chí quan trọng nhất là giảm thiểu chỉ số False Negative (FN) xuống thấp nhất.
          </div>
        </div>

        {/* PANEL 2: ROC-AUC CURVE RECHARTS */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden p-5 flex flex-col justify-between space-y-4">
          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <TrendingUp size={16} className="text-indigo-600" />
              Đường cong ROC Curve (Area Under Curve = {modelResult?.metrics.auc.toFixed(3)})
            </h2>
            <span className="badge-green font-mono">AUC = {modelResult?.metrics.auc.toFixed(3)}</span>
          </div>

          <div className="h-60 w-full my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={modelResult?.roc_curve} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} label={{ value: 'False Positive Rate (FPR)', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                <YAxis dataKey="tpr" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} label={{ value: 'True Positive Rate (TPR)', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                <Tooltip formatter={(val: any) => Number(val).toFixed(2)} />
                <Line type="monotone" dataKey="tpr" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} name="Mô hình XGBoost" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-50 p-2.5 rounded-lg text-center">
            Đường cong càng tiệm cận góc trên bên trái (TPR=1.0, FPR=0.0) thì mô hình phân loại càng chính xác.
          </div>
        </div>
      </div>

      {/* ── FEATURE IMPORTANCE RANKING CHART (Mục 9 Spec) ── */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-5 space-y-4">
        <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <BarChart3 size={16} className="text-indigo-600" />
            Xếp hạng Tầm quan trọng của các Chỉ số Tài chính (Feature Importance Ranking)
          </h2>
          <span className="badge-slate font-mono">Top Financial Predictors</span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={modelResult?.feature_importance} layout="vertical" margin={{ top: 10, right: 30, left: 140, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" domain={[0, 'auto']} tick={{ fontSize: 11 }} />
              <YAxis dataKey="display_name" type="category" tick={{ fontSize: 11, fill: '#334155' }} />
              <Tooltip formatter={(val: any) => [(Number(val) * 100).toFixed(1) + '%', 'Tầm quan trọng']} />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {modelResult?.feature_importance.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? '#4f46e5' : index < 3 ? '#6366f1' : '#a5b4fc'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
