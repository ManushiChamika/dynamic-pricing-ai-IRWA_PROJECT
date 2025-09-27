import React from 'react'
import { Link, NavLink } from 'react-router-dom'

export default function NavBar() {
  return (
    <header className="navbar">
      <div className="nav-inner">
        <div className="brand">
          <Link to="/" className="brand-link">FluxPricer AI</Link>
        </div>
        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Home</NavLink>
          <NavLink to="/pricing" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Pricing</NavLink>
        </nav>
        <div className="nav-actions">
          <Link to="/login" className="btn small">Login</Link>
          <Link to="/register" className="btn small primary">Register</Link>
        </div>
      </div>
    </header>
  )
}
