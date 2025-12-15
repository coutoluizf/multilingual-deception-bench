/**
 * Ethics page metadata.
 */
export const metadata = {
  title: 'Ethical Framework | Multilingual Deception Bench',
  description: 'Our ethical framework for AI safety research, responsible disclosure, and minimizing harm while measuring social engineering risk.',
}

/**
 * Ethics page component.
 * Explains the ethical framework and responsible disclosure policy.
 */
export default function EthicsPage() {
  return (
    <div className="space-y-12 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-100">Ethical Framework</h1>
        <p className="mt-2 text-slate-400">
          How we balance advancing AI safety research with minimizing potential harm.
        </p>
      </div>

      {/* Core Principles */}
      <section>
        <h2 className="text-xl font-bold text-slate-100 mb-4">Core Principles</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <PrincipleCard
            number={1}
            title="Minimize Harm"
            description="Every design decision prioritizes preventing the benchmark itself from being weaponized. We never publish actionable harmful content."
          />
          <PrincipleCard
            number={2}
            title="Advance Safety"
            description="Our goal is to improve AI safety, not to showcase vulnerabilities. Results are shared to help, not to harm."
          />
          <PrincipleCard
            number={3}
            title="Transparency"
            description="All methodology is open source and reproducible. We don't rely on security through obscurity."
          />
          <PrincipleCard
            number={4}
            title="Responsible Disclosure"
            description="Significant safety gaps are reported to AI providers before public disclosure, allowing time for remediation."
          />
        </div>
      </section>

      {/* What We Do */}
      <section className="bg-green-950/30 rounded-xl p-6 border border-green-900/50">
        <h2 className="text-xl font-bold text-green-400 mb-4">What We Do</h2>
        <ul className="space-y-3 text-slate-300">
          <li className="flex items-start gap-3">
            <span className="text-green-400 mt-1">✓</span>
            <span>
              <strong>Redact all harmful content:</strong> URLs, email addresses, phone numbers,
              real entity names are replaced with placeholders before storage
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-green-400 mt-1">✓</span>
            <span>
              <strong>Score in memory only:</strong> Raw model outputs are never written to disk
              or transmitted. Only aggregate metrics are stored.
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-green-400 mt-1">✓</span>
            <span>
              <strong>Focus on defense:</strong> Our goal is to help AI labs improve their
              safety measures, not to provide attack playbooks
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-green-400 mt-1">✓</span>
            <span>
              <strong>Collaborate with AI providers:</strong> We work with model providers
              to responsibly address findings before publication
            </span>
          </li>
        </ul>
      </section>

      {/* What We Don't Do */}
      <section className="bg-red-950/30 rounded-xl p-6 border border-red-900/50">
        <h2 className="text-xl font-bold text-red-400 mb-4">What We Don't Do</h2>
        <ul className="space-y-3 text-slate-300">
          <li className="flex items-start gap-3">
            <span className="text-red-400 mt-1">✗</span>
            <span>
              <strong>Publish working exploits:</strong> We never share complete, actionable
              social engineering content that could be directly used
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-red-400 mt-1">✗</span>
            <span>
              <strong>Store raw outputs:</strong> Model responses to sensitive prompts
              are never persisted in any form
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-red-400 mt-1">✗</span>
            <span>
              <strong>Name-and-shame:</strong> We don't use findings to embarrass AI providers.
              All results are presented constructively
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-red-400 mt-1">✗</span>
            <span>
              <strong>Provide attack tutorials:</strong> Our documentation explains what
              we measure, not how to attack systems
            </span>
          </li>
        </ul>
      </section>

      {/* Responsible Disclosure */}
      <section>
        <h2 className="text-xl font-bold text-slate-100 mb-4">Responsible Disclosure Policy</h2>
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6">
          <ol className="space-y-4 text-slate-300">
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">1</span>
              <div>
                <strong>Discovery:</strong> When we identify a significant safety gap in a model,
                we document it internally with full details.
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">2</span>
              <div>
                <strong>Private Notification:</strong> We contact the AI provider's security or
                safety team with our findings, including reproduction steps.
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">3</span>
              <div>
                <strong>Remediation Window:</strong> We provide at least 90 days for the provider
                to address the issue before including it in public results.
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">4</span>
              <div>
                <strong>Public Disclosure:</strong> After remediation (or after the disclosure
                window), we publish aggregate findings without actionable details.
              </div>
            </li>
          </ol>
        </div>
      </section>

      {/* Why This Matters */}
      <section>
        <h2 className="text-xl font-bold text-slate-100 mb-4">Why This Matters</h2>
        <div className="prose prose-invert max-w-none text-slate-300 space-y-4">
          <p>
            Social engineering attacks cause billions of dollars in damages annually and
            disproportionately affect vulnerable populations. As AI capabilities grow,
            so does the potential for AI-assisted social engineering.
          </p>
          <p>
            Portuguese and Spanish speakers—representing over 800 million people—are often
            underserved by AI safety research that focuses primarily on English. This benchmark
            helps ensure that safety improvements benefit all language communities equally.
          </p>
          <p>
            By providing rigorous, comparable data across languages, we help AI labs identify
            and address safety gaps before they can be exploited. Our approach is designed
            to be a force for good in the AI safety ecosystem.
          </p>
        </div>
      </section>

      {/* Contact */}
      <section className="bg-slate-900/50 rounded-xl p-6 border border-slate-800">
        <h2 className="text-xl font-bold text-slate-100 mb-4">Contact Us</h2>
        <p className="text-slate-400 mb-4">
          If you have questions about our ethical framework or want to report a concern:
        </p>
        <ul className="space-y-2 text-slate-300">
          <li>
            <strong>GitHub Issues:</strong>{' '}
            <a
              href="https://github.com/coutoluizf/multilingual-deception-bench/issues"
              className="text-blue-400 hover:text-blue-300"
              target="_blank"
              rel="noopener noreferrer"
            >
              Report an issue
            </a>
          </li>
          <li>
            <strong>Security concerns:</strong>{' '}
            Please use GitHub's private vulnerability reporting feature
          </li>
        </ul>
      </section>
    </div>
  )
}

/**
 * Principle card component.
 */
function PrincipleCard({
  number,
  title,
  description,
}: {
  number: number
  title: string
  description: string
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
          {number}
        </div>
        <h3 className="font-semibold text-slate-100">{title}</h3>
      </div>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  )
}
