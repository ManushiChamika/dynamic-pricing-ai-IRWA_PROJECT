import React from 'react'
import { motion } from 'framer-motion'
import { FiCheck, FiZap, FiFeather, FiTrendingUp, FiPhone } from 'react-icons/fi'
import NavBar from '../components/NavBar'

// Tiny helper: price label based on billing
const priceLabel = (plan, billing) => {
  if (plan.id === 'Custom') return 'Contact us'
  const value = billing === 'yearly' ? plan.priceYearly : plan.priceMonthly
  const suffix = billing === 'yearly' ? '/yr' : '/mo'
  return `$${value}${suffix}`
}

function Ribbon({ text = 'Popular' }) {
  return (
    <div style={{
      position: 'absolute',
      top: 12,
      right: 12,
      background: 'linear-gradient(135deg,#22d3ee,#2563eb)',
      color: '#fff',
      fontSize: 12,
      fontWeight: 700,
      padding: '6px 10px',
      borderRadius: 999,
      boxShadow: '0 4px 20px rgba(37,99,235,0.35)'
    }}>{text}</div>
  )
}

function Feature({ children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--muted, #475569)' }}>
      <FiCheck color="#10b981" />
      <span>{children}</span>
    </div>
  )
}

function ConfettiBurst({ burstKey }) {
  // Lightweight burst using framer-motion; no external deps
  const pieces = Array.from({ length: 18 })
  const colors = ['#22d3ee', '#2563eb', '#34d399', '#f59e0b', '#ef4444']
  return (
    <div key={burstKey} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
      {pieces.map((_, i) => {
        const delay = i * 0.02
        const x = (Math.random() - 0.5) * 200
        const y = -50 - Math.random() * 60
        const rot = (Math.random() - 0.5) * 120
        const color = colors[i % colors.length]
        return (
          <motion.div
            key={i}
            initial={{ opacity: 1, y: 0, x: 0, rotate: 0 }}
            animate={{ opacity: 0, y, x, rotate: rot }}
            transition={{ duration: 0.9, ease: 'easeOut', delay }}
            style={{
              position: 'absolute',
              left: '50%',
              top: '20%',
              width: 8,
              height: 12,
              background: color,
              borderRadius: 2,
              boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
            }}
          />
        )
      })}
    </div>
  )
}

function PlanCard({ plan, selected, onSelect, billing }) {
  const isSelected = selected === plan.id
  const Icon = plan.icon
  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 260, damping: 18 }}
      onClick={() => onSelect(plan.id)}
      role="button"
      aria-pressed={isSelected}
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(plan.id)}
      style={{
        position: 'relative',
        cursor: 'pointer',
        background: 'rgba(255,255,255,0.7)',
        backdropFilter: 'blur(6px)',
        borderRadius: 18,
        padding: 22,
        border: isSelected ? '2px solid #2563eb' : '1px solid rgba(0,0,0,0.08)',
        boxShadow: isSelected
          ? '0 16px 40px rgba(37,99,235,0.25)'
          : '0 10px 30px rgba(0,0,0,0.08)'
      }}
    >
      {plan.popular && <Ribbon />}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: 12,
          display: 'grid',
          placeItems: 'center',
          background: 'linear-gradient(135deg,#eff6ff,#dbeafe)',
          color: '#2563eb'
        }}>
          <Icon size={22} />
        </div>
        <div style={{ fontSize: 22, fontWeight: 800 }}>{plan.title}</div>
      </div>

      <div style={{ color: 'var(--muted, #64748b)', minHeight: 48 }}>{plan.description}</div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 14, marginBottom: 16 }}>
        <div style={{ fontSize: 28, fontWeight: 900 }}>{priceLabel(plan, billing)}</div>
        {plan.id !== 'Custom' && (
          <span style={{ color: '#64748b', fontSize: 12 }}>
            {billing === 'yearly' ? 'billed annually' : 'billed monthly'}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gap: 10 }}>
        {plan.features.map((f, idx) => (
          <Feature key={idx}>{f}</Feature>
        ))}
      </div>

      <button
        onClick={(e) => { e.stopPropagation(); onSelect(plan.id) }}
        style={{
          marginTop: 18,
          width: '100%',
          background: isSelected
            ? 'linear-gradient(135deg,#22d3ee,#2563eb)'
            : 'linear-gradient(135deg,#e2e8f0,#cbd5e1)',
          color: isSelected ? '#fff' : '#0f172a',
          border: 'none',
          padding: '12px 14px',
          borderRadius: 12,
          fontWeight: 800,
          letterSpacing: 0.3,
          cursor: 'pointer',
          boxShadow: isSelected ? '0 10px 30px rgba(37,99,235,0.35)' : 'none'
        }}
      >
        {isSelected ? 'Selected' : `Select ${plan.title}`}
      </button>
    </motion.div>
  )
}

export default function Pricing() {
  const [selected, setSelected] = React.useState(null)
  const [billing, setBilling] = React.useState('monthly') // 'monthly' | 'yearly'
  const [burstKey, setBurstKey] = React.useState(0)

  const plans = [
    {
      id: 'Basic',
      title: 'Basic',
  icon: FiFeather,
      priceMonthly: 19,
      priceYearly: 190,
      description: 'Essential features for individuals and small teams.',
      features: [
        'Up to 2 team members',
        'Core pricing tools',
        'Email support',
      ],
    },
    {
      id: 'Pro',
      title: 'Pro',
  icon: FiTrendingUp,
      priceMonthly: 49,
      priceYearly: 490,
      popular: true,
      description: 'Advanced features for growing businesses.',
      features: [
        'Unlimited team members',
        'Advanced analytics',
        'Priority support',
        'Workflow automations',
      ],
    },
    {
      id: 'Custom',
      title: 'Custom',
      icon: FiPhone,
      description: 'Tailored solutions for enterprises and unique needs.',
      features: [
        'Dedicated success manager',
        'Custom integrations',
        'SLA & Security reviews',
      ],
    },
  ]

  const handleSelect = (planId) => {
    setSelected(planId)
    setBurstKey((k) => k + 1)
  }

  const handleContinue = () => {
    if (!selected) {
      alert('Please choose a plan to continue')
      return
    }
    alert(`Selected plan: ${selected} (${billing})`)
  }

  return (
    <>
      <NavBar />
      <div
        style={{
          position: 'relative',
          minHeight: 'calc(100vh - 60px)',
          background: 'linear-gradient(180deg,#eef2ff 0%,#f8fafc 60%,#ffffff 100%)',
        }}
      >
        {/* Decorative gradient orbs */}
        <div aria-hidden style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
          <div style={{
            position: 'absolute',
            top: -80,
            left: -60,
            width: 280,
            height: 280,
            borderRadius: '50%',
            background: 'radial-gradient(circle at 30% 30%, rgba(34,211,238,0.35), transparent 60%)',
            filter: 'blur(4px)'
          }} />
          <div style={{
            position: 'absolute',
            bottom: -60,
            right: -60,
            width: 320,
            height: 320,
            borderRadius: '50%',
            background: 'radial-gradient(circle at 70% 70%, rgba(37,99,235,0.35), transparent 60%)',
            filter: 'blur(6px)'
          }} />
        </div>

        <div style={{ maxWidth: 1120, margin: '0 auto', padding: '32px 16px', position: 'relative' }}>
          {/* Hero */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              display: 'grid',
              placeItems: 'center',
              background: 'linear-gradient(135deg,#22d3ee,#2563eb)',
              color: '#fff',
              boxShadow: '0 8px 24px rgba(37,99,235,0.35)'
            }}>
              <FiZap />
            </div>
            <h1 style={{ fontSize: 32, margin: 0, fontWeight: 900 }}>Commercialize Plans</h1>
          </div>
          <p style={{ color: 'var(--muted,#64748b)', marginTop: 8, marginBottom: 18, maxWidth: 780 }}>
            Elevate your pricing workflow with modern tools and a delightful UX. Switch billing anytime.
          </p>

          {/* Benefits row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))',
            gap: 12,
            margin: '8px 0 12px',
          }}>
            {[
              'No credit card to start',
              'Cancel anytime',
              'Secure by default',
              'Fast, modern UI',
            ].map((b, i) => (
              <div key={i} style={{
                background: 'rgba(255,255,255,0.7)',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: 12,
                padding: '8px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                <FiCheck color="#10b981" />
                <span style={{ color: '#334155', fontSize: 13, fontWeight: 600 }}>{b}</span>
              </div>
            ))}
          </div>

          {/* Billing toggle */}
          <div
            aria-label="Billing period"
            role="tablist"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: 'rgba(255,255,255,0.7)',
              border: '1px solid rgba(0,0,0,0.08)',
              padding: 6,
              borderRadius: 999,
              boxShadow: '0 8px 24px rgba(0,0,0,0.06)'
            }}
          >
            {['monthly', 'yearly'].map((b) => (
              <button
                key={b}
                role="tab"
                aria-selected={billing === b}
                onClick={() => setBilling(b)}
                style={{
                  padding: '8px 14px',
                  borderRadius: 999,
                  border: 'none',
                  background: billing === b ? 'linear-gradient(135deg,#22d3ee,#2563eb)' : 'transparent',
                  color: billing === b ? '#fff' : '#0f172a',
                  fontWeight: 800,
                  cursor: 'pointer'
                }}
              >
                {b === 'monthly' ? 'Monthly' : 'Yearly'}
              </button>
            ))}
            {billing === 'yearly' && (
              <span style={{ marginLeft: 6, fontSize: 12, color: '#059669', fontWeight: 700 }}>Save 2 months</span>
            )}
          </div>

          {/* Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))',
              gap: 20,
              marginTop: 22,
              position: 'relative'
            }}
          >
            {plans.map((p) => (
              <PlanCard key={p.id} plan={p} selected={selected} onSelect={handleSelect} billing={billing} />)
            )}

            {/* Confetti overlay anchored to the grid area */}
            <ConfettiBurst burstKey={burstKey} />
          </div>

          {/* Simple compare section */}
          <div style={{ marginTop: 28, background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: 14, overflow: 'hidden' }}>
            <div style={{ padding: '10px 12px', fontWeight: 800, background: 'linear-gradient(180deg,#ffffff,#f1f5f9)' }}>
              Compare features
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr repeat(3, 1fr)' }}>
              {['Feature', 'Basic', 'Pro', 'Custom'].map((h, i) => (
                <div key={i} style={{ padding: '10px 12px', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>{h}</div>
              ))}
              {[
                ['Team members', '2', 'Unlimited', 'Unlimited'],
                ['Analytics', 'Core', 'Advanced', 'Custom'],
                ['Support', 'Email', 'Priority', 'Dedicated'],
              ].map((row, r) => (
                <React.Fragment key={r}>
                  <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>{row[0]}</div>
                  <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0' }}>{row[1]}</div>
                  <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0' }}>{row[2]}</div>
                  <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0' }}>{row[3]}</div>
                </React.Fragment>
              ))}
            </div>
          </div>

          <button
            onClick={handleContinue}
            disabled={!selected}
            style={{
              marginTop: 24,
              width: '100%',
              background: selected ? 'linear-gradient(135deg,#22d3ee,#2563eb)' : '#e2e8f0',
              color: selected ? '#fff' : '#94a3b8',
              border: 'none',
              padding: '14px 16px',
              borderRadius: 14,
              fontWeight: 900,
              letterSpacing: 0.3,
              cursor: selected ? 'pointer' : 'not-allowed',
              boxShadow: selected ? '0 12px 30px rgba(37,99,235,0.35)' : 'none'
            }}
          >
            {selected ? `Continue with ${selected}` : 'Continue'}
          </button>

          {/* FAQ */}
          <div style={{ marginTop: 26 }}>
            <h2 style={{ fontSize: 20, margin: '10px 0' }}>Frequently asked questions</h2>
            {[ 
              {
                q: 'Can I change plans later?',
                a: 'Yes, you can switch between monthly and yearly billing and change tiers at any time.'
              },
              {
                q: 'Do you offer trials?',
                a: 'We offer a risk-free start. You can explore core features before committing.'
              },
              {
                q: 'Is my data secure?',
                a: 'We follow best practices for encryption and data protection. Enterprise SLAs are available on Custom.'
              },
            ].map((item, idx) => (
              <details key={idx} style={{
                background: 'rgba(255,255,255,0.7)',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: 12,
                padding: '10px 12px',
                marginTop: 10
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: 700 }}>{item.q}</summary>
                <div style={{ color: '#475569', marginTop: 8 }}>{item.a}</div>
              </details>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
