export interface Company {
  ticker: string;
  name: string;
  exchange?: string;
  industry?: string;
  sector?: string;
  is_financial?: boolean;
  status?: 'LISTED' | 'DELISTED';
}

export interface PriceData {
  ticker: string;
  trading_date: string;
  close_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  ma20?: number;
  rsi_14?: number;
}

export interface IngestionResult {
  requested: number;
  passed: number;
  failed: number;
  raw_path: string;
  details: {
    ticker: string;
    status: 'PASS' | 'FAIL';
    message?: string;
  }[];
}

export interface PipelineResult {
  ingestion: IngestionResult;
}

export interface FinancialStatementItem {
  metric_code: string;
  metric_name: string;
  unit: string;
  category?: string;
  values: Record<string, number>;
}

export interface FinancialReportData {
  ticker: string;
  period_type: 'YEARLY' | 'QUARTERLY';
  periods: string[];
  balance_sheet: FinancialStatementItem[];
  income_statement: FinancialStatementItem[];
  cash_flow: FinancialStatementItem[];
}

export interface MetricMappingRule {
  standard_key: string;
  display_name: string;
  statement_type: 'BS' | 'IS' | 'CF';
  category: string;
  aliases: string[];
}

export interface DataQualityReport {
  total_companies: number;
  qualified_companies: number;
  rejected_companies: number;
  min_years_required: number;
  missing_rate_overall: number;
  missing_by_metric: Array<{
    metric_name: string;
    missing_count: number;
    missing_percentage: number;
  }>;
  outliers_detected: Array<{
    ticker: string;
    metric: string;
    year: string;
    raw_value: number;
    action: string;
  }>;
}

export interface FinancialRatios {
  ticker: string;
  year: string;
  // Liquidity
  current_ratio: number;
  working_capital_to_ta: number;
  ocf_to_current_liabilities: number;
  // Profitability
  roa: number;
  roe: number;
  ebit_margin: number;
  ebit_to_ta: number;
  asset_turnover: number;
  // Leverage
  short_term_debt_to_ta: number;
  long_term_debt_to_ta: number;
  debt_to_ta: number;
  // Size & Growth
  log_total_assets: number;
  asset_growth: number;
  profit_growth: number;
  market_cap: number;
  market_equity_to_debt: number;
  // Market & Technical Indicators
  sharpe_ratio: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  adx_14: number;
  cci_14: number;
}

export interface RuleDistressCheck {
  rule_code: string;
  rule_name: string;
  triggered: boolean;
  details: string;
}

export interface ZScoreComponents {
  x1_working_capital_to_ta: number;
  x2_retained_earnings_to_ta: number;
  x3_ebit_to_ta: number;
  x4_market_equity_to_debt: number;
  x5_sales_to_ta: number;
  z_score: number;
  zone: 'SAFE' | 'GREY' | 'DISTRESS';
}

export interface DistressLabelResult {
  ticker: string;
  year: string;
  final_label: 0 | 1;
  distress_status: 'SAFE' | 'WARNING' | 'DISTRESS';
  rule_based: {
    is_distress: boolean;
    triggered_rules: RuleDistressCheck[];
  };
  z_score_data: ZScoreComponents;
}

export interface DatasetRow {
  ticker: string;
  company_name: string;
  year: string;
  exchange: string;
  industry: string;
  roa: number;
  roe: number;
  current_ratio: number;
  debt_to_ta: number;
  ebit_margin: number;
  log_total_assets: number;
  z_score: number;
  distress_label: 0 | 1;
}

export interface FinalDatasetSummary {
  total_rows: number;
  total_companies: number;
  year_range: string;
  label_0_count: number;
  label_1_count: number;
  distress_ratio_pct: number;
  missing_rate_overall: number;
  file_size_estimates: {
    csv: string;
    excel: string;
    parquet: string;
  };
}

export interface ModelMetrics {
  auc: number;
  recall: number;
  precision: number;
  f1_score: number;
  accuracy: number;
  confusion_matrix: {
    tp: number;
    fp: number;
    tn: number;
    fn: number;
  };
}

export interface FeatureImportanceItem {
  feature_name: string;
  display_name: string;
  importance: number;
}

export interface ModelTrainingResult {
  model_name: string;
  train_years: string;
  test_years: string;
  metrics: ModelMetrics;
  feature_importance: FeatureImportanceItem[];
  roc_curve: Array<{ fpr: number; tpr: number }>;
}

export interface RiskFactor {
  factor_name: string;
  impact_type: 'POSITIVE' | 'NEGATIVE';
  impact_value: string;
  description: string;
}

export interface PredictionResult {
  ticker: string;
  company_name: string;
  year: string;
  distress_probability_pct: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH';
  z_score: number;
  z_zone: 'SAFE' | 'GREY' | 'DISTRESS';
  risk_factors: RiskFactor[];
  recommendations: string[];
  historical_probabilities: Array<{ year: string; probability: number }>;
}
