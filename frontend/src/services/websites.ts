import { fetchApi } from '../utils/api-client';
import { API_CONFIG } from '../config/api';

export interface Website {
  id: number;
  url: string;
  last_scraped_at: string | null;
  is_active: boolean;
  max_urls: number;
  scrape_interval_days: number;
}

interface WebsitesResponse {
  status: 'success' | 'error';
  data: {
    websites: Website[];
  };
  message?: string;
  error_code?: string;
}

export const websiteService = {
  getAll: async () => {
    const response = await fetchApi<WebsitesResponse>(API_CONFIG.ENDPOINTS.WEBSITES);
    if (response.status === 'error') {
      throw new Error(response.message || 'Failed to fetch websites');
    }
    return response.data.websites;
  },
}; 