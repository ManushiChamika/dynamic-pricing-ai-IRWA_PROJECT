import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { MessageSquare, BarChart3, Bell, ArrowRight, Zap } from 'lucide-react'

export function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#0F172A] text-white overflow-x-hidden">
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-[#0F172A]/80 backdrop-blur-lg">
        <div className="container mx-auto flex items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
              <Zap className="h-6 w-6 text-white fill-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">FluxPricer</span>
          </div>
          <div className="flex gap-3">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/auth')}
              className="text-gray-300 hover:text-white hover:bg-white/10"
            >
              Sign In
            </Button>
            <Button 
              onClick={() => navigate('/auth?mode=signup')}
              className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0"
            >
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      <main className="pt-24">
        <section className="relative overflow-hidden px-6 py-24 lg:py-32">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10" />
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }} />
          
          <div className="container mx-auto relative z-10">
            <div className="mx-auto max-w-4xl text-center">
              <div className="mb-8 inline-block">
                <span className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-300">
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
              
              <p className="mb-12 text-xl text-gray-400 md:text-2xl leading-relaxed max-w-3xl mx-auto">
                Let AI agents optimize your pricing in real-time. Control everything through natural language—no coding required.
              </p>
              
              <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center mb-12">
                <Button
                  size="lg"
                  className="text-lg h-14 px-10 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0 shadow-lg shadow-indigo-500/25"
                  onClick={() => navigate('/auth?mode=signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg h-14 px-10 border-white/20 text-white hover:bg-white/5 hover:border-white/40"
                  onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  Learn More
                </Button>
              </div>

              <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>No credit card</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>14-day free trial</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Cancel anytime</span>
                </div>
              </div>
            </div>

            <div className="mt-20 mx-auto max-w-5xl">
              <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-gray-800/50 to-gray-900/50 p-4 backdrop-blur-xl shadow-2xl">
                <div className="rounded-lg bg-[#1E293B] p-8 border border-white/5">
                  <div className="flex items-center gap-2 mb-6">
                    <div className="h-3 w-3 rounded-full bg-red-500"></div>
                    <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
                    <div className="h-3 w-3 rounded-full bg-green-500"></div>
                  </div>
                  <div className="space-y-4 text-left font-mono text-sm">
                    <div className="flex items-start gap-3">
                      <span className="text-indigo-400 font-semibold">You:</span>
                      <span className="text-gray-300">Show me pricing for laptops under $1000</span>
                    </div>
                    <div className="flex items-start gap-3">
                      <span className="text-purple-400 font-semibold">AI:</span>
                      <span className="text-gray-400">Analyzing 47 laptops... Found 3 competitors pricing below you. Recommend 8% decrease on Dell models.</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="px-6 py-24 bg-[#1E293B]/30 relative overflow-hidden">
          <div className="container mx-auto relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
              <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                Everything you need to optimize pricing and stay competitive
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
              <div className="group relative rounded-2xl border border-white/10 bg-gradient-to-br from-indigo-500/5 to-transparent p-8 transition-all hover:border-indigo-500/50 hover:shadow-lg hover:shadow-indigo-500/10">
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg shadow-indigo-500/25">
                  <MessageSquare className="h-7 w-7 text-white" />
                </div>
                <h3 className="mb-3 text-xl font-bold">Natural Language Control</h3>
                <p className="text-gray-400 leading-relaxed">
                  Chat with AI agents to adjust pricing strategies, set rules, and analyze market conditions—no code required.
                </p>
              </div>

              <div className="group relative rounded-2xl border border-white/10 bg-gradient-to-br from-purple-500/5 to-transparent p-8 transition-all hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10">
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 shadow-lg shadow-purple-500/25">
                  <BarChart3 className="h-7 w-7 text-white" />
                </div>
                <h3 className="mb-3 text-xl font-bold">Real-Time Market Intelligence</h3>
                <p className="text-gray-400 leading-relaxed">
                  Automated data collection from competitor sites, APIs, and search engines keeps you ahead of market changes.
                </p>
              </div>

              <div className="group relative rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/5 to-transparent p-8 transition-all hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10">
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/25">
                  <Bell className="h-7 w-7 text-white" />
                </div>
                <h3 className="mb-3 text-xl font-bold">Smart Alerts & Notifications</h3>
                <p className="text-gray-400 leading-relaxed">
                  Get notified via email, Slack, or SMS when market conditions change or opportunities arise.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="px-6 py-24 relative overflow-hidden">
          <div className="container mx-auto max-w-5xl relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">How It Works</h2>
              <p className="text-xl text-gray-400">Get started in minutes, not weeks</p>
            </div>

            <div className="relative">
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
                  const styles: Record<string, { card: string; hover: string; dot: string; shadow: string }> = {
                    indigo: { card: 'from-indigo-500/5', hover: 'hover:border-indigo-500/50', dot: 'from-indigo-500 to-indigo-600', shadow: 'shadow-indigo-500/25' },
                    purple: { card: 'from-purple-500/5', hover: 'hover:border-purple-500/50', dot: 'from-purple-500 to-purple-600', shadow: 'shadow-purple-500/25' },
                    pink: { card: 'from-pink-500/5', hover: 'hover:border-pink-500/50', dot: 'from-pink-500 to-pink-600', shadow: 'shadow-pink-500/25' },
                    emerald: { card: 'from-emerald-500/5', hover: 'hover:border-emerald-500/50', dot: 'from-emerald-500 to-emerald-600', shadow: 'shadow-emerald-500/25' },
                  }
                  return steps.map((step, idx) => {
                    const c = styles[step.color]
                    return (
                      <div key={step.num} className={`flex gap-8 items-center ${idx % 2 === 1 ? 'md:flex-row-reverse' : ''}`}>
                        <div className="flex-1 text-center md:text-right">
                          <div className={`inline-block rounded-2xl border border-white/10 bg-gradient-to-br ${c.card} to-transparent p-6 transition-all ${c.hover}`}>
                            <h3 className="text-2xl font-bold mb-2">{step.title}</h3>
                            <p className="text-gray-400">{step.desc}</p>
                          </div>
                        </div>
                        <div className={`relative z-10 flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${c.dot} text-2xl font-bold shadow-lg ${c.shadow}`}>
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

        <section className="px-6 py-24 bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10">
          <div className="container mx-auto max-w-4xl text-center">
            <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Pricing?</h2>
            <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
              Join businesses using AI to stay competitive and maximize revenue
            </p>
            <Button
              size="lg"
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

      <footer className="border-t border-white/10 bg-[#0F172A] py-12">
        <div className="container mx-auto px-6">
          <div className="flex flex-col items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <Zap className="h-5 w-5 text-white fill-white" />
              </div>
              <span className="text-xl font-bold">FluxPricer</span>
            </div>
            <p className="text-gray-500 text-sm">&copy; 2025 FluxPricer. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
