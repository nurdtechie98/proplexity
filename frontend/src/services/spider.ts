import { fetchApi } from '../utils/api-client';
import { API_CONFIG } from '../config/api';

interface SpiderStartRequest {
  start_url: string;
  max_urls: number;
  batch_size: number;
}

interface SpiderStartResponse {
  status: 'success' | 'error';
  data?: {
    job_id: string;
    status: string;
  };
  message?: string;
  error_code?: string;
}

interface SpiderStatusResponse {
  status: 'success' | 'error' | 'in_progress';
  data?: {
    status: string;
    progress?: number;
  };
  message?: string;
  error_code?: string;
  progress?: number;
}

export const spiderService = {
  startScraping: (data: SpiderStartRequest) => 
    fetchApi<SpiderStartResponse>(API_CONFIG.ENDPOINTS.SPIDER.START, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getStatus: (jobId: string) =>
    fetchApi<SpiderStatusResponse>(API_CONFIG.ENDPOINTS.SPIDER.STATUS(jobId)),
}; 