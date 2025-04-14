"use client";

import { useState } from 'react';
import WebsiteList from '../components/WebsiteList';
import AddWebsiteForm from '../components/AddWebsiteForm';

export default function WebsitesPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="mt-8">
          <WebsiteList key={refreshKey} />
        </div>
      </div>
    </div>
  );
}