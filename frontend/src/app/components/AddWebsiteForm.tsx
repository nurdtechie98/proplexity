"use client";

import { useState } from 'react';
import { spiderService } from '../../services/spider';

interface AddWebsiteFormProps {
  onSuccess?: () => void;
}

export default function AddWebsiteForm({ onSuccess }: AddWebsiteFormProps) {
  const [url, setUrl] = useState('');
  const [maxUrls, setMaxUrls] = useState('100');
  const [batchSize, setBatchSize] = useState('20');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const data = await spiderService.startScraping({
        start_url: url,
        max_urls: parseInt(maxUrls),
        batch_size: parseInt(batchSize)
      });
      
      setJobStatus('Spider started successfully! Tracking progress...');
      
      // Poll for spider status
      const pollInterval = setInterval(async () => {
        try {
          const statusData = await spiderService.getStatus(data.data?.job_id || '');
          setJobStatus(`Scraping status: ${statusData.status}${
            statusData.progress ? ` (${statusData.progress}% complete)` : ''
          }`);
          
          if (['success', 'error'].includes(statusData.status)) {
            clearInterval(pollInterval);
            if (statusData.status === 'success') {
              setJobStatus('Website scraping completed successfully!');
              onSuccess?.();
            } else if (statusData.status === 'error') {
              setError(statusData.message || 'Scraping failed');
            }
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError(err instanceof Error ? err.message : 'Failed to get status');
        }
      }, 2000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start website scraping');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Track New Website</h1>
      <form onSubmit={handleSubmit} className="max-w-lg space-y-6">
        <div>
          <label className="block text-sm font-semibold text-gray-900 mb-1">Website URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="mt-1 block w-full px-4 py-3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900 placeholder-gray-500"
            placeholder="https://example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-900 mb-1">Max URLs to Scrape</label>
          <input
            type="number"
            value={maxUrls}
            onChange={(e) => setMaxUrls(e.target.value)}
            required
            min="1"
            className="mt-1 block w-full px-4 py-3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-900 mb-1">Batch Size</label>
          <input
            type="number"
            value={batchSize}
            onChange={(e) => setBatchSize(e.target.value)}
            required
            min="1"
            className="mt-1 block w-full px-4 py-3 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-gray-900"
          />
          <p className="mt-1 text-sm text-gray-600">Number of URLs to process in each batch</p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 font-medium"
        >
          {loading ? 'Starting Spider...' : 'Start Scraping'}
        </button>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-md font-medium">{error}</div>
        )}

        {jobStatus && (
          <div className="bg-green-50 text-green-700 p-4 rounded-md font-medium">{jobStatus}</div>
        )}
      </form>
    </div>
  );
}