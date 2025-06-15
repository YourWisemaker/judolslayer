import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'JudolSlayer - YouTube Spam Comment Remover',
  description: 'AI-powered tool to detect and remove online gambling spam comments from YouTube videos',
  keywords: ['YouTube', 'spam', 'comments', 'AI', 'gambling', 'judol', 'moderation'],
  authors: [{ name: 'JudolSlayer Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#3b82f6',
  openGraph: {
    title: 'JudolSlayer - YouTube Spam Comment Remover',
    description: 'AI-powered tool to detect and remove online gambling spam comments from YouTube videos',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JudolSlayer - YouTube Spam Comment Remover',
    description: 'AI-powered tool to detect and remove online gambling spam comments from YouTube videos',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 antialiased`}>
        <Providers>
          <div className="min-h-full">
            <header className="bg-white shadow-sm border-b border-gray-200">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <h1 className="text-2xl font-bold text-primary-600">
                        🛡️ JudolSlayer
                      </h1>
                    </div>
                    <div className="hidden md:block ml-4">
                      <p className="text-sm text-gray-600">
                        AI-Powered YouTube Spam Comment Remover
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="hidden sm:flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-sm text-gray-600">Online</span>
                    </div>
                  </div>
                </div>
              </div>
            </header>
            
            <main className="flex-1">
              {children}
            </main>
            
            <footer className="bg-white border-t border-gray-200 mt-auto">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="flex flex-col md:flex-row justify-between items-center">
                  <div className="text-sm text-gray-600">
                    © 2024 JudolSlayer. Powered by Gemini AI & LangGraph.
                  </div>
                  <div className="flex items-center space-x-4 mt-4 md:mt-0">
                    <span className="text-xs text-gray-500">
                      Made with ❤️ for cleaner YouTube comments
                    </span>
                  </div>
                </div>
              </div>
            </footer>
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}