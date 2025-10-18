import { getHowItWorksCard } from '../../lib/themeHelpers'

interface HowItWorksSectionProps {
  isDark: boolean
  mutedText: string
}

interface Step {
  num: number
  title: string
  desc: string
  color: 'indigo' | 'purple' | 'pink' | 'emerald'
}

const steps: Step[] = [
  {
    num: 1,
    title: 'Connect Your Store',
    desc: 'Link your product catalog and set initial pricing rules in minutes',
    color: 'indigo',
  },
  {
    num: 2,
    title: 'AI Learns Your Market',
    desc: 'Our agents collect competitor data and analyze market trends automatically',
    color: 'purple',
  },
  {
    num: 3,
    title: 'Chat to Control',
    desc: 'Use natural language to adjust strategies and review insights',
    color: 'pink',
  },
  {
    num: 4,
    title: 'Optimize & Grow',
    desc: 'Watch as AI continuously improves your pricing performance',
    color: 'emerald',
  },
]

export function HowItWorksSection({ isDark, mutedText }: HowItWorksSectionProps) {
  return (
    <section className="px-6 py-24 relative overflow-hidden">
      <div className="container mx-auto max-w-5xl relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">How It Works</h2>
          <p className={`text-xl ${mutedText}`}>Get started in minutes, not weeks</p>
        </div>

        <div className="relative">
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
            {steps.map((step, idx) => {
              const palette = getHowItWorksCard(step.color, isDark)
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
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
