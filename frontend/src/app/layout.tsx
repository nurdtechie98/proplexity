import './globals.css';
import { ReactNode } from 'react';
import Navigation from './components/Navigation';

export const metadata = {
  title: 'Proplexity - AI Search',
  description: 'Archive and chat with your web content',
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navigation />
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}