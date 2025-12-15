import Link from 'next/link'

/**
 * Landing page for the Multilingual Deception Bench.
 * Introduces the project and links to key sections.
 */
export default function HomePage() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          <span className="gradient-text">Multilingual</span>{' '}
          <span className="text-slate-100">Deception Bench</span>
        </h1>
        <p className="mt-6 text-xl text-slate-400 max-w-3xl mx-auto">
          An open-source benchmark for measuring AI-enabled social engineering
          risk across Portuguese, Spanish, and English.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/leaderboard"
            className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-blue-500 transition-colors"
          >
            View Leaderboard
          </Link>
          <Link
            href="/methodology"
            className="rounded-lg border border-slate-600 px-6 py-3 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Methodology
          </Link>
        </div>
      </section>

      {/* Mission Statement */}
      <section className="bg-slate-900/50 rounded-2xl p-8 border border-slate-800">
        <h2 className="text-2xl font-bold text-slate-100 mb-4">Our Mission</h2>
        <p className="text-slate-400 leading-relaxed">
          Social engineering attacks are increasingly being enhanced by AI capabilities.
          While English-language safety research is well-funded, Portuguese and Spanish
          speakers - representing over 800 million people - are often overlooked.
          This benchmark provides rigorous, comparable data on how different AI models
          respond to social engineering prompts across languages, helping AI labs,
          policymakers, and researchers make informed decisions about AI safety.
        </p>
      </section>

      {/* Key Features */}
      <section>
        <h2 className="text-2xl font-bold text-slate-100 mb-8 text-center">
          What We Measure
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Feature cards */}
          <FeatureCard
            title="Refusal Rate"
            description="How often does the model refuse to generate harmful content? Higher is safer."
            icon="🛡️"
          />
          <FeatureCard
            title="Soft Refusal Rate"
            description="Partial compliance with warnings - indicates safety awareness but incomplete guardrails."
            icon="⚠️"
          />
          <FeatureCard
            title="Compliance Rate"
            description="Full compliance with deceptive requests - lower is safer."
            icon="📊"
          />
          <FeatureCard
            title="Cultural Adaptation"
            description="How well does the model adapt harmful content to local contexts?"
            icon="🌍"
          />
          <FeatureCard
            title="Language Quality"
            description="Grammar and fluency in non-English languages affects persuasiveness."
            icon="📝"
          />
          <FeatureCard
            title="Cross-Lingual Consistency"
            description="Do safety measures work equally well across all languages?"
            icon="🔄"
          />
        </div>
      </section>

      {/* Attack Types */}
      <section>
        <h2 className="text-2xl font-bold text-slate-100 mb-8 text-center">
          Attack Types Covered
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <AttackTypeCard type="Phishing" />
          <AttackTypeCard type="Bank Impersonation" />
          <AttackTypeCard type="Delivery Scams" />
          <AttackTypeCard type="Government Fraud" />
          <AttackTypeCard type="Tech Support Scams" />
        </div>
      </section>

      {/* CTA Section */}
      <section className="text-center py-12 bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-2xl border border-slate-800">
        <h2 className="text-2xl font-bold text-slate-100 mb-4">
          Contribute to AI Safety
        </h2>
        <p className="text-slate-400 mb-8 max-w-2xl mx-auto">
          MDB is open source and welcomes contributions from researchers,
          developers, and AI safety advocates worldwide.
        </p>
        <a
          href="https://github.com/coutoluizf/multilingual-deception-bench"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-6 py-3 text-sm font-semibold text-slate-100 hover:bg-slate-700 transition-colors"
        >
          <GitHubIcon />
          View on GitHub
        </a>
      </section>
    </div>
  )
}

/**
 * Feature card component for displaying benchmark features.
 */
function FeatureCard({
  title,
  description,
  icon
}: {
  title: string
  description: string
  icon: string
}) {
  return (
    <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-800 card-hover">
      <div className="text-3xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-slate-100 mb-2">{title}</h3>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  )
}

/**
 * Attack type card component.
 */
function AttackTypeCard({ type }: { type: string }) {
  return (
    <div className="bg-slate-900/50 rounded-lg px-4 py-3 text-center border border-slate-800 hover:border-slate-600 transition-colors">
      <span className="text-sm font-medium text-slate-300">{type}</span>
    </div>
  )
}

/**
 * GitHub icon component.
 */
function GitHubIcon() {
  return (
    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
      <path
        fillRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        clipRule="evenodd"
      />
    </svg>
  )
}
