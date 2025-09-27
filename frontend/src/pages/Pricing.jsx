import React from 'react'
import NavBar from '../components/NavBar'

export default function Pricing() {
  return (
    <>
      <NavBar />
      <div className="container" style={{ textAlign: 'center' }}>
        <h1 className="title" style={{ fontSize: 40 }}>Pricing</h1>
        <p className="subtitle">Choose the plan that fits your team</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginTop: 24 }}>
          <div className="hero-image" style={{ height: 220 }}>Starter</div>
          <div className="hero-image" style={{ height: 220 }}>Pro</div>
          <div className="hero-image" style={{ height: 220 }}>Enterprise</div>
        </div>
      </div>
    </>
  )
}
