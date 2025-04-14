"use client";

import { useState } from 'react';
import { retrievalService, RetrievalResult } from '../../services/retrieval';

export default function Chat() {
  const [query, setQuery] = useState('');
  const [urlPrefix, setUrlPrefix] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RetrievalResult | null>(null);

  const performSearch = async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await retrievalService.search({
        query: searchQuery,
        num_results: 10,
        url_prefix: urlPrefix || undefined,
      });
      console.log(typeof data);
      setResult(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await performSearch(query);
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Search</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4 mb-8">
        <div>
          <label htmlFor="query" className="block text-sm font-semibold text-gray-900 mb-1">
            Search Query
          </label>
          <input
            type="text"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
            placeholder="Enter your question..."
            required
          />
        </div>
        
        <div>
          <label htmlFor="urlPrefix" className="block text-sm font-semibold text-gray-900 mb-1">
            URL Prefix (Optional)
          </label>
          <input
            type="text"
            id="urlPrefix"
            value={urlPrefix}
            onChange={(e) => setUrlPrefix(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
            placeholder="Filter by URL prefix..."
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 font-medium"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4 font-medium">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold mb-3 text-gray-900">Answer</h2>
            <p className="text-gray-900 whitespace-pre-wrap text-base">{result.answer}</p>
          </div>

          {result.sources.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-3 text-gray-900">Sources</h2>
              <div className="space-y-4">
                {result.sources.map((source, index) => (
                  <div key={index} className="border-b last:border-b-0 pb-4 last:pb-0">
                    <a href={source.url} target="_blank" rel="noopener noreferrer" 
                       className="text-blue-700 hover:underline block mb-2 font-medium">
                      {source.url}
                    </a>
                    <p className="text-gray-800 text-base bg-gray-50 p-3 rounded-md">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.follow_up_questions.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-3 text-gray-900">Follow-up Questions</h2>
              <ul className="space-y-2">
                {result.follow_up_questions.map((question, index) => (
                  <li key={index} 
                      className="text-blue-700 cursor-pointer hover:underline font-medium"
                      onClick={async () => {
                        setQuery(question);
                        window.scrollTo(0, 0);
                        // Trigger new search with this question
                        setLoading(true);
                        setError(null);
                        setResult(null);

                        try {
                          const response = await retrievalService.search({
                            query: question,
                            num_results: 10,
                            url_prefix: urlPrefix || undefined,
                          });
                          setResult(response.data);
                        } catch (err) {
                          setError(err instanceof Error ? err.message : 'An error occurred');
                        } finally {
                          setLoading(false);
                        }
                      }}>
                    {question}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 