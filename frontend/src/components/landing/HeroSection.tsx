import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/button'
import { ArrowRight, MessageSquare } from 'lucide-react'
import { CheckmarkItem } from './CheckmarkItem'
import { useAuthUser } from '../../stores/authStore'

interface HeroSectionProps {
  isDark: boolean
  heroGradient: string
  dottedOverlay: string
  mutedText: string
  softMutedText: string
  secondaryCta: string
}

export function HeroSection({
  isDark,
  heroGradient,
  dottedOverlay,
  mutedText,
  softMutedText,
  secondaryCta,
}: HeroSectionProps) {
  const navigate = useNavigate()
  const user = useAuthUser()

  return (
    <section className="relative overflow-hidden px-6 py-24 lg:py-32">
      <div className={`absolute inset-0 bg-gradient-to-br ${heroGradient}`} />
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

          <p className={`mb-12 text-xl md:text-2xl leading-relaxed max-w-3xl mx-auto text-center ${mutedText}`}>
            Let AI agents optimize your pricing in real-time. Control everything through natural
            language—no coding required.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row mb-12">
            {user ? (
              <Button
                className="text-lg h-14 px-10 leading-none bg-gradient-to-r from-indigo-500 to-purple-600 text-white border border-transparent shadow-[0_18px_40px_rgba(79,70,229,0.25)]"
                onClick={() => navigate('/chat')}
              >
                Go to Chat
                <MessageSquare className="ml-2 h-5 w-5" />
              </Button>
            ) : (
              <>
                <Button
                  className="text-lg h-14 px-10 leading-none bg-gradient-to-r from-indigo-500 to-purple-600 text-white border border-transparent shadow-[0_18px_40px_rgba(79,70,229,0.25)]"
                  onClick={() => navigate('/auth?mode=signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button
                  className={`${secondaryCta} leading-none`}
                  onClick={() =>
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
                  }
                >
                  Learn More
                </Button>
              </>
            )}
          </div>

          <div className={`flex items-center justify-center gap-8 text-sm ${softMutedText}`}>
            <CheckmarkItem text="No credit card" />
            <CheckmarkItem text="14-day free trial" />
            <CheckmarkItem text="Cancel anytime" />
          </div>
        </div>

        <div className="mt-20 mx-auto max-w-6xl">
          <div className="flex items-end gap-6">
            <div className="flex-shrink-0 w-80">
              <img
                src="/robot-mascot.png"
                alt="FluxPricer AI Assistant"
                className="w-full h-auto object-contain"
                style={{ marginBottom: '-80px' }}
              />
            </div>

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
  )
}
