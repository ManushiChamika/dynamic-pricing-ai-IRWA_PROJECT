import React from 'react'
import { Link } from 'react-router-dom'
import NavBar from '../components/NavBar'

export default function Landing() {
  return (
    <>
      <NavBar />

      {/* Hero Section */}
      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-content">
            <div className="eyebrow-badge">New · Governance‑ready pricing AI</div>
            <h1 className="title">Meet <span className="title-accent">FluxPricer AI</span></h1>
            <p className="subtitle">
              AI-powered dynamic pricing platform to simulate, propose, and apply prices with built‑in
              guardrails, approvals, and a complete audit trail.
            </p>
            <div className="cta-row">
              <Link to="/login" className="btn primary btn-lg">Get started</Link>
              <a href="#features" className="btn secondary btn-lg">Explore features</a>
            </div>
            <div className="stat-row">
              <div className="stat">
                <div className="value">10k+</div>
                <div className="label">SKUs optimized</div>
              </div>
              <div className="stat">
                <div className="value">ms‑latency</div>
                <div className="label">Realtime updates</div>
              </div>
              <div className="stat">
                <div className="value">100%</div>
                <div className="label">Audit coverage</div>
              </div>
            </div>
          </div>
          <div className="hero-visual">
            <img
              src="/dynamic-pricing-hero.png"
              alt="Dynamic Pricing AI model illustration"
              loading="eager"
            />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="features container">
        <div className="feature-grid">
          <div className="card hoverable">
            <div className="icon">📈</div>
            <h3>AI Price Optimization</h3>
            <p>Optimize prices using ML and market signals for maximum revenue and margin.</p>
          </div>
          <div className="card hoverable">
            <div className="icon">🔔</div>
            <h3>Real-time Alerts</h3>
            <p>Notify operators on key events and proposals; surface updates instantly.</p>
          </div>
          <div className="card hoverable">
            <div className="icon">🧭</div>
            <h3>Governance & Guardrails</h3>
            <p>AutoApplier with guardrails ensures safe application with full audit trail.</p>
          </div>
          <div className="card hoverable">
            <div className="icon">📝</div>
            <h3>Decision Log</h3>
            <p>Persistent audit: who changed what, when, and why—fully observable.</p>
          </div>
        </div>
      </section>

      {/* Pricing placeholder */}
      <section id="pricing" className="container" style={{ textAlign: 'center' }}>
        <h2 style={{ color: '#1f2937' }}>Pricing</h2>
        <p className="subtitle">Starter, Pro, and Enterprise tiers (placeholder)</p>
      </section>

      <div className="footer">© 2025 FluxPricer AI</div>
    </>
  )
}
