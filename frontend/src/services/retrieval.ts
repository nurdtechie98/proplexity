import { fetchApi } from '../utils/api-client';
import { API_CONFIG } from '../config/api';

export interface RetrievalResult {
  answer: string;
  sources: Array<{
    url: string;
    text: string;
  }>;
  follow_up_questions: string[];
}

interface RetrievalRequest {
  query: string;
  num_results: number;
  url_prefix?: string;
}

interface RetrievalResponse {
  status: string;
  data: RetrievalResult;
}

export const retrievalService = {
  search: (data: RetrievalRequest) =>
    fetchApi<RetrievalResponse>(API_CONFIG.ENDPOINTS.RETRIEVAL, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}; 