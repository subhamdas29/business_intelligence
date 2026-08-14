import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Business Intelligence Platform',
  description: 'Enterprise AI Data Analyst SaaS Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        {children}
      </body>
    </html>
  );
}
