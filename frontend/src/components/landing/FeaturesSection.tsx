import { MessageSquare, BarChart3, Bell } from 'lucide-react'

interface FeaturesSectionProps {
  isDark: boolean
  mutedText: string
  secondarySurface: string
  featureCardBase: string
}

export function FeaturesSection({
  isDark,
  mutedText,
  secondarySurface,
  featureCardBase,
}: FeaturesSectionProps) {
  return (
    <section id="features" className={`px-6 py-24 ${secondarySurface} relative overflow-hidden`}>
      <div className="container mx-auto relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
          <p className={`text-xl ${mutedText} max-w-2xl mx-auto text-center`}>
            Everything you need to optimize pricing and stay competitive
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
          <div
            className={`${featureCardBase} ${
              isDark
                ? 'from-indigo-500/5 to-transparent hover:border-indigo-500/50 hover:shadow-lg hover:shadow-indigo-500/10'
                : 'bg-white hover:border-indigo-500/30 hover:shadow-[0_20px_45px_rgba(79,70,229,0.16)]'
            } group p-8 transition-all`}
          >
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg shadow-indigo-500/25">
              <MessageSquare className="h-7 w-7 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold">Natural Language Control</h3>
            <p className={`${mutedText} leading-relaxed`}>
              Chat with AI agents to adjust pricing strategies, set rules, and analyze market
              conditions—no code required.
            </p>
          </div>

          <div
            className={`${featureCardBase} ${
              isDark
                ? 'from-purple-500/5 to-transparent hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10'
                : 'bg-white hover:border-purple-500/30 hover:shadow-[0_20px_45px_rgba(147,51,234,0.16)]'
            } group p-8 transition-all`}
          >
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 shadow-lg shadow-purple-500/25">
              <BarChart3 className="h-7 w-7 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold">Real-Time Market Intelligence</h3>
            <p className={`${mutedText} leading-relaxed`}>
              Automated data collection from competitor sites, APIs, and search engines keeps you
              ahead of market changes.
            </p>
          </div>

          <div
            className={`${featureCardBase} ${
              isDark
                ? 'from-emerald-500/5 to-transparent hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10'
                : 'bg-white hover:border-emerald-500/30 hover:shadow-[0_20px_45px_rgba(16,185,129,0.18)]'
            } group p-8 transition-all`}
          >
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/25">
              <Bell className="h-7 w-7 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold">Smart Alerts & Notifications</h3>
            <p className={`${mutedText} leading-relaxed`}>
              Get notified via email, Slack, or SMS when market conditions change or opportunities
              arise.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}


