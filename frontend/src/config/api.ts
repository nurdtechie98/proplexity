export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'https://c250e5ad-0603-4bbf-b214-11ff640610f6-00-uapw7uwex9nu.sisko.replit.dev:8000',
  ENDPOINTS: {
    WEBSITES: '/websites',
    SPIDER: {
      START: '/scraper/spider/start',
      STATUS: (jobId: string) => `/scraper/spider/${jobId}/status`,
    },
    RETRIEVAL: '/retrieval',
  },
}; 