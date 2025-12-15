import './globals.css'
import type { Metadata } from 'next'
import { Navigation } from '@/components/Navigation'

// Metadata for SEO
export const metadata: Metadata = {
  title: 'Multilingual Deception Bench | AI Safety Benchmark',
  description: 'An open-source benchmark for measuring AI-enabled social engineering risk across languages. Compare how different AI models respond to deceptive prompts.',
  keywords: ['AI safety', 'benchmark', 'social engineering', 'LLM', 'multilingual', 'deception'],
  authors: [{ name: 'Multilingual Deception Bench Contributors' }],
  openGraph: {
    title: 'Multilingual Deception Bench',
    description: 'Measuring AI safety across languages',
    type: 'website',
  },
}

/**
 * Root layout component for the Next.js app.
 * Provides consistent navigation and styling across all pages.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {/* Navigation header */}
        <Navigation />

        {/* Main content area */}
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 bg-slate-950 py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
              <p className="text-sm text-slate-400">
                Multilingual Deception Bench - Open Source AI Safety Research
              </p>
              <div className="flex gap-4">
                <a
                  href="https://github.com/coutoluizf/multilingual-deception-bench"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-slate-400 hover:text-slate-100"
                >
                  GitHub
                </a>
                <a
                  href="/ethics"
                  className="text-sm text-slate-400 hover:text-slate-100"
                >
                  Ethics
                </a>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
