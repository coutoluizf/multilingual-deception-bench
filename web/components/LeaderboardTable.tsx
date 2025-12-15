'use client'

import Link from 'next/link'
import { useState } from 'react'

/**
 * Model result data structure.
 */
export interface ModelResult {
  id: string
  name: string
  provider: string
  refusalRate: number
  softRefusalRate: number
  complianceRate: number
  avgLatency: number
  totalExamples: number
  byLanguage: {
    pt: { refusalRate: number; complianceRate: number }
    es: { refusalRate: number; complianceRate: number }
    en: { refusalRate: number; complianceRate: number }
  }
}

/**
 * Sort configuration.
 */
type SortKey = 'name' | 'refusalRate' | 'softRefusalRate' | 'complianceRate' | 'avgLatency'
type SortDirection = 'asc' | 'desc'

/**
 * Props for the LeaderboardTable component.
 */
interface LeaderboardTableProps {
  models: ModelResult[]
}

/**
 * Leaderboard table component.
 * Displays a sortable comparison table of model results.
 */
export function LeaderboardTable({ models }: LeaderboardTableProps) {
  // Sort state
  const [sortKey, setSortKey] = useState<SortKey>('refusalRate')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  // Handle column header click for sorting
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // New column, default to desc (higher is better for refusal)
      setSortKey(key)
      setSortDirection(key === 'complianceRate' || key === 'avgLatency' ? 'asc' : 'desc')
    }
  }

  // Sort models
  const sortedModels = [...models].sort((a, b) => {
    const aVal = a[sortKey]
    const bVal = b[sortKey]

    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }

    return sortDirection === 'asc'
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number)
  })

  // Helper to format percentages
  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`

  // Helper to get color class based on value
  const getRefusalColor = (value: number) => {
    if (value >= 0.8) return 'text-green-400'
    if (value >= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getComplianceColor = (value: number) => {
    if (value <= 0.2) return 'text-green-400'
    if (value <= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Sort indicator
  const SortIndicator = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return null
    return (
      <span className="ml-1">
        {sortDirection === 'asc' ? '↑' : '↓'}
      </span>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/50">
      <table className="w-full leaderboard-table">
        <thead className="bg-slate-800/50">
          <tr>
            <th className="w-8 text-center">#</th>
            <th
              className="cursor-pointer hover:bg-slate-700/50"
              onClick={() => handleSort('name')}
            >
              Model <SortIndicator column="name" />
            </th>
            <th
              className="cursor-pointer hover:bg-slate-700/50 text-center"
              onClick={() => handleSort('refusalRate')}
            >
              Refusal Rate <SortIndicator column="refusalRate" />
            </th>
            <th
              className="cursor-pointer hover:bg-slate-700/50 text-center"
              onClick={() => handleSort('softRefusalRate')}
            >
              Soft Refusal <SortIndicator column="softRefusalRate" />
            </th>
            <th
              className="cursor-pointer hover:bg-slate-700/50 text-center"
              onClick={() => handleSort('complianceRate')}
            >
              Compliance <SortIndicator column="complianceRate" />
            </th>
            <th
              className="cursor-pointer hover:bg-slate-700/50 text-center"
              onClick={() => handleSort('avgLatency')}
            >
              Avg Latency <SortIndicator column="avgLatency" />
            </th>
            <th className="text-center">Samples</th>
          </tr>
        </thead>
        <tbody>
          {sortedModels.map((model, index) => (
            <tr key={model.id} className="hover:bg-slate-800/30">
              <td className="text-center text-slate-500 font-mono">
                {index + 1}
              </td>
              <td>
                <Link
                  href={`/models/${model.id}`}
                  className="font-medium text-slate-100 hover:text-blue-400 transition-colors"
                >
                  {model.name}
                </Link>
                <div className="text-xs text-slate-500">{model.provider}</div>
              </td>
              <td className="text-center">
                <span className={`font-mono ${getRefusalColor(model.refusalRate)}`}>
                  {formatPercent(model.refusalRate)}
                </span>
              </td>
              <td className="text-center">
                <span className="font-mono text-yellow-400">
                  {formatPercent(model.softRefusalRate)}
                </span>
              </td>
              <td className="text-center">
                <span className={`font-mono ${getComplianceColor(model.complianceRate)}`}>
                  {formatPercent(model.complianceRate)}
                </span>
              </td>
              <td className="text-center font-mono text-slate-400">
                {model.avgLatency.toFixed(0)}ms
              </td>
              <td className="text-center text-slate-500">
                {model.totalExamples}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Empty state */}
      {sortedModels.length === 0 && (
        <div className="py-12 text-center text-slate-400">
          No evaluation results available yet.
        </div>
      )}
    </div>
  )
}

/**
 * Language breakdown table for a single model.
 */
export function LanguageBreakdownTable({ model }: { model: ModelResult }) {
  const languages = [
    { code: 'pt', name: 'Portuguese', data: model.byLanguage.pt },
    { code: 'es', name: 'Spanish', data: model.byLanguage.es },
    { code: 'en', name: 'English', data: model.byLanguage.en },
  ]

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="w-full leaderboard-table">
        <thead className="bg-slate-800/50">
          <tr>
            <th>Language</th>
            <th className="text-center">Refusal Rate</th>
            <th className="text-center">Compliance Rate</th>
          </tr>
        </thead>
        <tbody>
          {languages.map((lang) => (
            <tr key={lang.code}>
              <td className="font-medium">{lang.name}</td>
              <td className="text-center font-mono">
                {(lang.data.refusalRate * 100).toFixed(1)}%
              </td>
              <td className="text-center font-mono">
                {(lang.data.complianceRate * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
