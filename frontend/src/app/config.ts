export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const endpoints = {
  websites: `${API_BASE_URL}/api/websites`,
  chat: `${API_BASE_URL}/api/chat`,
  jobs: (jobId: string) => `${API_BASE_URL}/api/jobs/${jobId}`,
}; 