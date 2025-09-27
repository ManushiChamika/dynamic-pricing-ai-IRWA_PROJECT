import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FiMail, FiLock, FiUser, FiEye, FiEyeOff, FiArrowRight, FiCheck, FiAlertCircle } from 'react-icons/fi'
import { API_URL } from '../config'

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const MIN_PASSWORD = 10

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [focusedField, setFocusedField] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isSubmitting) return
    
    setError('')
    setSuccess('')

    const trimmedEmail = email.trim().toLowerCase()
    const trimmedPassword = password.trim()
    const trimmedUsername = username.trim()

    if (!trimmedUsername) {
      setError('Please enter your name.')
      return
    }

    if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
      setError('Please enter a valid email address.')
      return
    }

    if (!trimmedPassword || trimmedPassword.length < MIN_PASSWORD) {
      setError(`Password must be at least ${MIN_PASSWORD} characters.`)
      return
    }

    setIsSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: trimmedEmail, password: trimmedPassword, username: trimmedUsername })
      })
      const data = await res.json()
      if (!res.ok || !data?.ok) throw new Error(data?.detail || 'Registration failed')

      // Do NOT auto-login. Send user back to landing to login explicitly.
      setSuccess('Registration successful! Please log in to continue.')
      setTimeout(() => {
        window.location.href = '/'
      }, 2000)
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="login-container">
      <motion.div 
        className="login-card"
        initial={{ opacity: 0, y: 30, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <motion.div 
          className="login-header"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="login-icon">
            <motion.div
              initial={{ rotate: -10, scale: 0.8 }}
              animate={{ rotate: 0, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.5, ease: "easeOut" }}
            >
              ✨
            </motion.div>
          </div>
          <h1>Create Account</h1>
          <p>Join FluxPricer AI and start optimizing</p>
        </motion.div>

        <AnimatePresence mode="wait">
          {error && (
            <motion.div 
              className="alert error"
              initial={{ opacity: 0, x: -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.95 }}
              transition={{ duration: 0.3 }}
            >
              <FiAlertCircle />
              <span>{error}</span>
            </motion.div>
          )}
          {success && (
            <motion.div 
              className="alert success"
              initial={{ opacity: 0, x: -20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.95 }}
              transition={{ duration: 0.3 }}
            >
              <FiCheck />
              <span>{success}</span>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.form 
          onSubmit={handleSubmit} 
          className="login-form"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="form-group">
            <label htmlFor="username">Full Name</label>
            <div className={`input-wrapper ${focusedField === 'username' ? 'focused' : ''}`}>
              <FiUser className="input-icon" />
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setFocusedField('username')}
                onBlur={() => setFocusedField(null)}
                placeholder="Your full name"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className={`input-wrapper ${focusedField === 'email' ? 'focused' : ''}`}>
              <FiMail className="input-icon" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setFocusedField('email')}
                onBlur={() => setFocusedField(null)}
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className={`input-wrapper ${focusedField === 'password' ? 'focused' : ''}`}>
              <FiLock className="input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusedField('password')}
                onBlur={() => setFocusedField(null)}
                placeholder="••••••••••"
                required
                minLength={MIN_PASSWORD}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            <small style={{ color: '#64748b', fontSize: '12px' }}>
              Minimum {MIN_PASSWORD} characters required
            </small>
          </div>

          <motion.button
            type="submit"
            className="login-btn"
            disabled={isSubmitting}
            whileHover={{ scale: isSubmitting ? 1 : 1.02 }}
            whileTap={{ scale: isSubmitting ? 1 : 0.98 }}
            transition={{ duration: 0.2 }}
          >
            {isSubmitting ? (
              <motion.div
                className="loading-spinner"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              />
            ) : (
              <>
                Create Account
                <FiArrowRight className="btn-icon" />
              </>
            )}
          </motion.button>

          <div className="form-footer">
            <Link to="/" className="back-link">
              ← Back to Home
            </Link>
            <span className="divider">•</span>
            <Link to="/login" className="signup-link">
              Sign In
            </Link>
          </div>
        </motion.form>
      </motion.div>
    </div>
  )
}
