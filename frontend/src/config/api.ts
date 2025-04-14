export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    WEBSITES: '/websites',
    SPIDER: {
      START: '/scraper/spider/start',
      STATUS: (jobId: string) => `/scraper/spider/${jobId}/status`,
    },
    RETRIEVAL: '/retrieval',
  },
}; 