"use client";

import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { websiteService, Website } from '../../services/websites';
import { spiderService } from '../../services/spider';

export default function WebsiteList() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scrapingStatus, setScrapingStatus] = useState<Record<string, string>>({});

  const fetchWebsites = async () => {
    try {
      const data = await websiteService.getAll();
      setWebsites(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch websites');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWebsites();
  }, []);

  const handleRefresh = async (website: Website) => {
    try {
      setScrapingStatus(prev => ({ ...prev, [website.id]: 'starting' }));
      
      // Start scraping
      const response = await spiderService.startScraping({
        start_url: website.url,
        max_urls: website.max_urls,
        batch_size: 10 // You might want to make this configurable
      });

      if (response.status !== 'success' || !response.data?.job_id) {
        throw new Error('Failed to start scraping: Invalid response');
      }

      // Poll for status
      const checkStatus = async () => {
        const statusResponse = await spiderService.getStatus(response.data?.job_id || '');
        
        if (!statusResponse || typeof statusResponse !== 'object') {
          throw new Error('Invalid status response');
        }

        if (statusResponse.status === 'success') {
          setScrapingStatus(prev => ({ ...prev, [website.id]: 'completed' }));
          // Refresh the website list to get updated data
          fetchWebsites();
        } else if (statusResponse.status === 'error' || statusResponse.data?.status === 'failed') {
          setScrapingStatus(prev => ({ ...prev, [website.id]: 'failed' }));
        } else {
          const progress = statusResponse.data?.progress || 0;
          setScrapingStatus(prev => ({ 
            ...prev, 
            [website.id]: `in progress (${progress}%)`
          }));
          setTimeout(checkStatus, 2000); // Poll every 2 seconds
        }
      };

      checkStatus();
    } catch (err) {
      setScrapingStatus(prev => ({ ...prev, [website.id]: 'failed' }));
      setError(err instanceof Error ? err.message : 'Failed to start scraping');
    }
  };

  if (loading) return <div className="flex justify-center p-8">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Tracked Websites</h1>
      <div className="grid gap-4">
        {websites.map((website) => (
          <div key={website.id} className="bg-white p-4 rounded-lg shadow">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-semibold text-blue-700">{website.url}</h2>
                <div className="mt-2 text-base text-gray-900">
                  <p>Last scraped: {website.last_scraped_at ? 
                    format(new Date(website.last_scraped_at), 'PPpp') : 
                    'Never'}</p>
                  <p>Scrape interval: {website.scrape_interval_days} days</p>
                  <p>Max URLs: {website.max_urls}</p>
                  <p>Status: {website.is_active ? 
                    <span className="text-green-600 font-medium">Active</span> : 
                    <span className="text-red-600 font-medium">Inactive</span>}</p>
                  {scrapingStatus[website.id] && (
                    <p>Scraping status: <span className="font-medium">{scrapingStatus[website.id]}</span></p>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleRefresh(website)}
                disabled={scrapingStatus[website.id]?.includes('progress')}
                className={`px-4 py-2 rounded-md ${
                  scrapingStatus[website.id]?.includes('progress')
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                {scrapingStatus[website.id]?.includes('progress') ? 'Scraping...' : 'Refresh'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 