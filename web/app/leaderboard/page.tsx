import { LeaderboardTable } from '@/components/LeaderboardTable'
import { getModelResults } from '@/lib/data'

/**
 * Leaderboard page metadata.
 */
export const metadata = {
  title: 'Leaderboard | Multilingual Deception Bench',
  description: 'Compare AI model safety metrics across languages. See how different models respond to social engineering prompts.',
}

/**
 * Leaderboard page component.
 * Displays the main comparison table of all evaluated models.
 */
export default function LeaderboardPage() {
  // Get all model results
  const models = getModelResults()

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Model Leaderboard</h1>
        <p className="mt-2 text-slate-400">
          Compare how different AI models respond to social engineering prompts
          across Portuguese, Spanish, and English.
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-green-400" />
          <span className="text-slate-400">Safe (high refusal / low compliance)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-yellow-400" />
          <span className="text-slate-400">Moderate</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-red-400" />
          <span className="text-slate-400">Concerning (low refusal / high compliance)</span>
        </div>
      </div>

      {/* Main leaderboard table */}
      <LeaderboardTable models={models} />

      {/* Methodology note */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-2">
          How to Interpret These Results
        </h2>
        <ul className="space-y-2 text-sm text-slate-400">
          <li>
            <strong className="text-slate-300">Refusal Rate:</strong> Higher is better.
            Indicates how often the model refuses to generate potentially harmful content.
          </li>
          <li>
            <strong className="text-slate-300">Soft Refusal:</strong> Partial compliance with warnings.
            Some soft refusal is expected, but high rates may indicate inconsistent guardrails.
          </li>
          <li>
            <strong className="text-slate-300">Compliance:</strong> Lower is better.
            Full compliance with deceptive requests indicates potential for misuse.
          </li>
          <li>
            <strong className="text-slate-300">Cross-lingual consistency:</strong>{' '}
            Click on a model to see how safety varies across languages.
          </li>
        </ul>
      </div>

      {/* Data freshness note */}
      <p className="text-xs text-slate-500">
        Results last updated: December 2024. Evaluations run on {models[0]?.totalExamples || 100} examples per model.
      </p>
    </div>
  )
}
