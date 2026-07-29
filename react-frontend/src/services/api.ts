import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export class ApiClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiClientError';
  }
}

apiClient.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    let detail = '';
    if (error.response?.data) {
      const data = error.response.data as any;
      detail = `: ${data.detail || JSON.stringify(data)}`;
    } else {
      detail = `: ${error.message}`;
    }
    throw new ApiClientError(`Backend request failed (${error.config?.method?.toUpperCase()} ${error.config?.url})${detail}`);
  }
);

// --- API Functions ---

export const getHealth = async (): Promise<any> => {
  return apiClient.get('/health', { timeout: 5000 });
};

export const getCompanies = async (limit = 100): Promise<any> => {
  return apiClient.get('/companies', { params: { page: 1, limit } });
};

export const getPrices = async (
  ticker: string,
  startDate?: string,
  endDate?: string,
  limit = 1000
): Promise<any> => {
  const params: Record<string, any> = { ticker, page: 1, limit };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return apiClient.get('/prices', { params });
};

export const runPipeline = async (
  tickers: string[],
  startDate: string,
  endDate: string,
  interval = '1D'
): Promise<any> => {
  return apiClient.post(
    '/pipeline/run',
    {
      tickers,
      start_date: startDate,
      end_date: endDate,
      interval,
    },
    { timeout: 180000 }
  );
};
