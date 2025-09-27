import React from 'react'
import { Link } from 'react-router-dom'
import NavBar from '../components/NavBar'

export default function Landing() {
  return (
    <>
      <NavBar />
      <div className="container">
        <div className="hero">
          <div className="hero-inner">
            <div style={{ fontSize: 72, marginBottom: 0 }}>🚀</div>
            <h1 className="title">Meet <span>FluxPricer AI</span></h1>
            <p className="subtitle">AI-powered dynamic pricing platform for modern businesses</p>
            <div className="hero-image">
              {/* Replace with your actual hero image later */}
              Beautiful dashboard preview
            </div>
            <section className="features container">
              <div className="feature-grid">
                <div className="card">
                  <div className="icon">📈</div>
                  <h3>AI Price Optimization</h3>
                  <p>Optimize prices using ML and market signals for maximum revenue and margin.</p>
                </div>
                <div className="card">
                  <div className="icon">🔔</div>
                  <h3>Real-time Alerts</h3>
                  <p>Notify operators on key events and proposals; surface updates instantly.</p>
                </div>
                <div className="card">
                  <div className="icon">🧭</div>
                  <h3>Governance & Guardrails</h3>
                  <p>AutoApplier with guardrails ensures safe application with full audit trail.</p>
                </div>
                <div className="card">
                  <div className="icon">📝</div>
                  <h3>Decision Log</h3>
                  <p>Persistent audit: who changed what, when, and why—fully observable.</p>
                </div>
              </div>
            </section>
          </div>
        </div>

      <section id="pricing" className="container" style={{ textAlign: 'center' }}>
        <h2 style={{ color: '#1f2937' }}>Pricing</h2>
        <p className="subtitle">Starter, Pro, and Enterprise tiers (placeholder)</p>
      </section>

      <div className="footer">© 2025 FluxPricer AI</div>
      </div>
    </>
  )
}
