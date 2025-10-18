import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { MessageSquare, BarChart3, Bell, ArrowRight } from 'lucide-react'
import { Navigation } from '../components/Navigation'
import { Footer } from '../components/Footer'
import { useTheme } from '../contexts/ThemeContext'

export function LandingPage() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const pageClasses = isDark ? 'bg-[#0F172A] text-white' : 'bg-slate-50 text-slate-900'
  const mutedText = isDark ? 'text-gray-400' : 'text-slate-700'
  const softMutedText = isDark ? 'text-gray-500' : 'text-slate-600'
  const sectionBackdrop = isDark ? 'bg-[#1E293B]/30' : 'bg-slate-100'
  const gradientOverlay = isDark
    ? 'from-indigo-500/10 via-transparent to-purple-500/10'
    : 'from-indigo-400/15 via-transparent to-purple-300/10'
  const dottedOverlay = isDark
    ? 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)'
    : 'radial-gradient(circle at 1px 1px, rgba(79,70,229,0.08) 1px, transparent 0)'
  const secondaryCta = isDark
    ? 'text-lg h-14 px-10 border border-white/20 text-white hover:bg-white/10 hover:border-white/40'
    : 'text-lg h-14 px-10 border border-slate-300 bg-white/85 text-slate-800 hover:bg-slate-100 hover:border-slate-400'

  const featureCardBase = isDark
    ? 'relative rounded-2xl border border-white/10 bg-gradient-to-br'
    : 'relative rounded-2xl border border-slate-200 bg-white shadow-[0_18px_40px_rgba(15,23,42,0.12)]'

  const howItWorksCard = (color: 'indigo' | 'purple' | 'pink' | 'emerald') => {
    const palette: Record<
      typeof color,
      { card: string; hover: string; dot: string; shadow: string; hoverShadow: string }
    > = {
      indigo: {
        card: isDark ? 'from-indigo-500/5' : 'from-indigo-50',
        hover: isDark ? 'hover:border-indigo-500/50' : 'hover:border-indigo-500/40',
        dot: isDark ? 'from-indigo-500 to-indigo-600' : 'from-indigo-500 to-indigo-600',
        shadow: isDark ? 'shadow-indigo-500/25' : 'shadow-indigo-500/30',
        hoverShadow: isDark
          ? 'hover:shadow-lg hover:shadow-indigo-500/10'
          : 'hover:shadow-[0_24px_55px_rgba(79,70,229,0.15)]',
      },
      purple: {
        card: isDark ? 'from-purple-500/5' : 'from-purple-50',
        hover: isDark ? 'hover:border-purple-500/50' : 'hover:border-purple-500/40',
        dot: 'from-purple-500 to-purple-600',
        shadow: isDark ? 'shadow-purple-500/25' : 'shadow-purple-500/30',
        hoverShadow: isDark
          ? 'hover:shadow-lg hover:shadow-purple-500/10'
          : 'hover:shadow-[0_24px_55px_rgba(147,51,234,0.16)]',
      },
      pink: {
        card: isDark ? 'from-pink-500/5' : 'from-pink-50',
        hover: isDark ? 'hover:border-pink-500/50' : 'hover:border-pink-500/40',
        dot: 'from-pink-500 to-pink-600',
        shadow: isDark ? 'shadow-pink-500/25' : 'shadow-pink-500/30',
        hoverShadow: isDark
          ? 'hover:shadow-lg hover:shadow-pink-500/10'
          : 'hover:shadow-[0_24px_55px_rgba(236,72,153,0.14)]',
      },
      emerald: {
        card: isDark ? 'from-emerald-500/5' : 'from-emerald-50',
        hover: isDark ? 'hover:border-emerald-500/50' : 'hover:border-emerald-500/40',
        dot: 'from-emerald-500 to-emerald-600',
        shadow: isDark ? 'shadow-emerald-500/25' : 'shadow-emerald-500/30',
        hoverShadow: isDark
          ? 'hover:shadow-lg hover:shadow-emerald-500/10'
          : 'hover:shadow-[0_24px_55px_rgba(16,185,129,0.14)]',
      },
    }

    return palette[color]
  }

  return (
    <div className={pageClasses}>
      <Navigation />

      <main className="pt-24">
        <section className="relative overflow-hidden px-6 py-24 lg:py-32">
          <div className={`absolute inset-0 bg-gradient-to-br ${gradientOverlay}`} />
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: dottedOverlay,
              backgroundSize: '40px 40px',
            }}
          />

          <div className="container mx-auto relative z-10">
            <div className="mx-auto max-w-4xl text-center">
              <div className="mb-8 inline-block">
                <span
                  className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium ${
                    isDark
                      ? 'border-indigo-500/20 bg-indigo-500/10 text-indigo-300'
                      : 'border-indigo-500/30 bg-white/80 text-indigo-700 shadow-[0_10px_25px_rgba(79,70,229,0.12)]'
                  }`}
                >
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                  </span>
                  AI-Powered Pricing Platform
                </span>
              </div>

              <h1 className="mb-8 text-5xl font-extrabold leading-tight tracking-tight md:text-6xl lg:text-7xl">
                Dynamic Pricing Made{' '}
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Simple
                </span>
              </h1>

              <p
                className={`mb-12 text-xl md:text-2xl leading-relaxed max-w-3xl mx-auto ${mutedText}`}
              >
                Let AI agents optimize your pricing in real-time. Control everything through natural
                language—no coding required.
              </p>

              <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center mb-12">
                <Button
                  className="text-lg h-14 px-10 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0 shadow-[0_18px_40px_rgba(79,70,229,0.25)]"
                  onClick={() => navigate('/auth?mode=signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button
                  className={secondaryCta}
                  onClick={() =>
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
                  }
                >
                  Learn More
                </Button>
              </div>

              <div className={`flex items-center justify-center gap-8 text-sm ${softMutedText}`}>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>No credit card</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>14-day free trial</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Cancel anytime</span>
                </div>
              </div>
            </div>

            <div className="mt-20 mx-auto max-w-6xl">
              <div className="flex items-end gap-6">
                {/* Robot Image - Left Side */}
                <div className="flex-shrink-0 w-80">
                  <img
                    src="/robot-mascot.png"
                    alt="FluxPricer AI Assistant"
                    className="w-full h-auto object-contain"
                    style={{ marginBottom: '-80px' }}
                  />
                </div>

                {/* Chat Demo - Right Side */}
                <div className="flex-1">
                  <div
                    className={`rounded-2xl border p-4 backdrop-blur-xl shadow-2xl ${
                      isDark
                        ? 'border-white/10 bg-gradient-to-br from-slate-800/50 to-slate-900/50'
                        : 'border-slate-200 bg-white/95 shadow-[0_24px_60px_rgba(15,23,42,0.18)]'
                    }`}
                  >
                    <div
                      className={`rounded-lg p-8 border ${isDark ? 'bg-[#1E293B] border-white/5' : 'bg-slate-50 border-slate-200'}`}
                    >
                      <div className="flex items-center gap-2 mb-6">
                        <div className="h-3 w-3 rounded-full bg-red-500"></div>
                        <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
                        <div className="h-3 w-3 rounded-full bg-green-500"></div>
                      </div>
                      <div className="space-y-4 text-left font-mono text-sm">
                        <div className="flex items-start gap-3">
                          <span className="text-indigo-500 font-semibold">You:</span>
                          <span className={isDark ? 'text-gray-300' : 'text-slate-700'}>
                            Show me pricing for laptops under $1000
                          </span>
                        </div>
                        <div className="flex items-start gap-3">
                          <span className="text-purple-500 font-semibold">AI:</span>
                          <span className={mutedText}>
                            Analyzing 47 laptops... Found 3 competitors pricing below you. Recommend
                            8% decrease on Dell models.
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className={`px-6 py-24 ${sectionBackdrop} relative overflow-hidden`}>
          <div className="container mx-auto relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
              <p className={`text-xl ${mutedText} max-w-2xl mx-auto`}>
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
                  Automated data collection from competitor sites, APIs, and search engines keeps
                  you ahead of market changes.
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
                  Get notified via email, Slack, or SMS when market conditions change or
                  opportunities arise.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 py-24 relative overflow-hidden">
          <div className="container mx-auto max-w-5xl relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">How It Works</h2>
              <p className={`text-xl ${mutedText}`}>Get started in minutes, not weeks</p>
            </div>

            <div className="relative">
              {/* Robot Image - Right Side, Above Step 2 */}
              <div
                className="hidden md:block absolute z-0"
                style={{ top: '-20rem', right: '-8rem' }}
              >
                <img
                  src="/robot-mascot1.png"
                  alt="AI Robot"
                  className="object-contain"
                  style={{ width: '37rem', height: '36rem', opacity: 0.95 }}
                />
              </div>
              <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-indigo-500 via-purple-500 to-pink-500 hidden md:block" />

              <div className="space-y-12">
                {(() => {
                  const steps = [
                    {
                      num: 1,
                      title: 'Connect Your Store',
                      desc: 'Link your product catalog and set initial pricing rules in minutes',
                      color: 'indigo' as const,
                    },
                    {
                      num: 2,
                      title: 'AI Learns Your Market',
                      desc: 'Our agents collect competitor data and analyze market trends automatically',
                      color: 'purple' as const,
                    },
                    {
                      num: 3,
                      title: 'Chat to Control',
                      desc: 'Use natural language to adjust strategies and review insights',
                      color: 'pink' as const,
                    },
                    {
                      num: 4,
                      title: 'Optimize & Grow',
                      desc: 'Watch as AI continuously improves your pricing performance',
                      color: 'emerald' as const,
                    },
                  ]
                  return steps.map((step, idx) => {
                    const palette = howItWorksCard(step.color)
                    const cardSurface = isDark
                      ? `border-white/10 bg-gradient-to-br ${palette.card} to-transparent`
                      : 'border-slate-200 bg-white shadow-[0_18px_40px_rgba(15,23,42,0.12)]'
                    return (
                      <div
                        key={step.num}
                        className={`flex gap-8 items-center ${idx % 2 === 1 ? 'md:flex-row-reverse' : ''}`}
                      >
                        <div className="flex-1 text-center md:text-right">
                          <div
                            className={`inline-block rounded-2xl border p-6 transition-all ${cardSurface} ${palette.hover} ${palette.hoverShadow}`}
                          >
                            <h3 className="text-2xl font-bold mb-2">{step.title}</h3>
                            <p className={mutedText}>{step.desc}</p>
                          </div>
                        </div>
                        <div
                          className={`relative z-10 flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${palette.dot} text-2xl font-bold shadow-lg ${palette.shadow}`}
                        >
                          {step.num}
                        </div>
                        <div className="flex-1" />
                      </div>
                    )
                  })
                })()}
              </div>
            </div>
          </div>
        </section>

        <section
          className={`px-6 py-24 bg-gradient-to-br ${
            isDark
              ? 'from-indigo-500/10 via-purple-500/10 to-pink-500/10'
              : 'from-indigo-100 via-purple-100 to-pink-100'
          }`}
        >
          <div className="container mx-auto max-w-4xl text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Pricing?</h2>
            <p className={`text-xl ${mutedText} mb-10 max-w-2xl mx-auto`}>
              Join businesses using AI to stay competitive and maximize revenue
            </p>
            <Button
              className="text-lg h-16 px-12 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0 shadow-lg shadow-indigo-500/25"
              onClick={() => navigate('/auth?mode=signup')}
            >
              Get Started Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <p className="mt-6 text-sm text-gray-500">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
