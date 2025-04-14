'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex-shrink-0">
            <Link href="/" className="text-xl font-bold text-blue-600">
              Proplexity
            </Link>
          </div>
          <div className="flex space-x-8">
            <Link
              href="/"
              className={`${
                pathname === '/'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium`}
            >
              Search
            </Link>
            <Link
              href="/websites"
              className={`${
                pathname === '/websites'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium`}
            >
              View Websites
            </Link>
            <Link
              href="/add"
              className={`${
                pathname === '/add'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium`}
            >
              Add Website
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
} 