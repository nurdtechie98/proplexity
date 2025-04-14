"use client";

import WebsiteList from '../components/WebsiteList';

export default function WebsitesPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="mt-8">
          <WebsiteList />
        </div>
      </div>
    </div>
  );
}