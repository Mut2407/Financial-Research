export interface Company {
  ticker: string;
  name: string;
  exchange?: string;
  industry?: string;
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
