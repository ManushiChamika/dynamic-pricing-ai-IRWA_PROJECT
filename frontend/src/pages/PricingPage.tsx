import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Navigation } from '../components/Navigation'
import { Footer } from '../components/Footer'
import { ArrowRight, Check } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { getPageThemeClasses, getPlanCardBase } from '../lib/themeHelpers'

export function PricingPage() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const { pageClasses, mutedText, helperText, heroGradient, dottedOverlay, secondarySurface } =
    getPageThemeClasses(isDark)
  const planCardBase = getPlanCardBase(isDark)

  const plans = [
    {
      name: 'Starter',
      description: 'Perfect for small businesses',
      price: '$29',
      period: '/month',
      features: [
        'Up to 100 SKUs',
        'Basic competitor tracking',
        'Email notifications',
        'API access',
        'Community support',
        '7-day data history',
      ],
      highlighted: false,
    },
    {
      name: 'Professional',
      description: 'For growing ecommerce businesses',
      price: '$99',
      period: '/month',
      features: [
        'Unlimited SKUs',
        'Advanced competitor tracking',
        'Real-time alerts',
        'REST & GraphQL APIs',
        'Priority support',
        '90-day data history',
        'Custom pricing rules',
        'Multi-channel support',
      ],
      highlighted: true,
    },
    {
      name: 'Enterprise',
      description: 'For large-scale operations',
      price: 'Custom',
      period: 'pricing',
      features: [
        'Everything in Professional',
        'Dedicated account manager',
        'Custom integrations',
        'Unlimited data history',
        'SLA guarantee',
        'On-premise deployment',
        'Advanced analytics',
        'Custom AI training',
      ],
      highlighted: false,
    },
  ]

  return (
    <div className={pageClasses}>
      <Navigation />

      <main className="pt-24">
        <section
          className={`relative overflow-hidden px-6 py-24 lg:py-32 ${isDark ? 'bg-[#0F172A]' : 'bg-slate-100/60'}`}
        >
          <div className={`absolute inset-0 bg-gradient-to-br ${heroGradient}`} />
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: dottedOverlay,
              backgroundSize: '40px 40px',
            }}
          />

          <div className="container mx-auto relative z-10">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="mb-6 text-5xl font-extrabold leading-tight tracking-tight md:text-6xl">
                Simple, Transparent{' '}
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Pricing
                </span>
              </h1>

              <p
                className={`mb-12 text-xl md:text-2xl leading-relaxed max-w-3xl mx-auto ${mutedText}`}
              >
                Choose the perfect plan for your business. Scale up anytime as your needs grow.
              </p>
            </div>
          </div>
        </section>

        <section className={`px-6 py-24 ${secondarySurface}`}>
          <div className="container mx-auto">
            <div className="grid gap-8 md:grid-cols-3 max-w-7xl mx-auto">
              {plans.map((plan, idx) => (
                <div
                  key={idx}
                  className={`${planCardBase} ${
                    plan.highlighted
                      ? `border-indigo-500 shadow-2xl shadow-indigo-500/25 transform scale-105 ${
                          isDark
                            ? 'bg-gradient-to-br from-indigo-500/10 to-purple-500/10'
                            : 'bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100'
                        }`
                      : isDark
                        ? 'border-white/10 bg-[#1E293B]/50 hover:border-indigo-500/35'
                        : 'hover:border-indigo-500/30 hover:shadow-[0_24px_55px_rgba(79,70,229,0.16)]'
                  }`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                        Most Popular
                      </span>
                    </div>
                  )}

                  <div className="p-8">
                    <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                    <p className={`text-sm mb-6 ${mutedText}`}>{plan.description}</p>

                    <div className="mb-6">
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold">{plan.price}</span>
                        <span className={`text-sm ${helperText}`}>{plan.period}</span>
                      </div>
                    </div>

                    <Button
                      onClick={() => navigate('/auth?mode=signup')}
                      className={`w-full mb-8 h-11 ${
                        plan.highlighted
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0'
                          : isDark
                            ? 'bg-white/10 hover:bg-white/20 text-white border border-white/15'
                            : 'bg-white hover:bg-slate-100 text-slate-800 border border-slate-300'
                      }`}
                    >
                      Get Started
                      <ArrowRight className="h-4 w-4" />
                    </Button>

                    <div className="space-y-4">
                      {plan.features.map((feature, fidx) => (
                        <div key={fidx} className="flex items-start gap-3">
                          <Check className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                          <span
                            className={`text-sm ${isDark ? 'text-gray-300' : 'text-slate-700'}`}
                          >
                            {feature}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div
              className={`mt-16 max-w-3xl mx-auto rounded-2xl border ${isDark ? 'border-white/10 bg-[#1E293B]/50' : 'border-slate-200 bg-white'} p-8 shadow-[0_20px_45px_rgba(15,23,42,0.1)]`}
            >
              <h3 className="text-2xl font-bold mb-4">Frequently Asked Questions</h3>

              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">Can I change plans anytime?</h4>
                  <p className={mutedText}>
                    Yes! You can upgrade, downgrade, or cancel your plan at any time. Changes take
                    effect at the next billing cycle.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Is there a free trial?</h4>
                  <p className={mutedText}>
                    Absolutely! Get 14 days free to try any plan. No credit card required.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">What payment methods do you accept?</h4>
                  <p className={mutedText}>
                    We accept all major credit cards, bank transfers, and digital payment methods.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Do you offer annual discounts?</h4>
                  <p className={mutedText}>
                    Yes! Annual plans come with 20% savings. Contact our sales team for enterprise
                    discounts.
                  </p>
                </div>
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
            <h2 className="text-4xl font-bold mb-6">Need a custom plan?</h2>
            <p className={`text-xl mb-10 max-w-2xl mx-auto ${mutedText}`}>
              For enterprise customers with unique requirements, we offer customized solutions.
            </p>
            <Button
              onClick={() => navigate('/contact')}
              className="h-12 px-8 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0"
            >
              Contact Sales
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
