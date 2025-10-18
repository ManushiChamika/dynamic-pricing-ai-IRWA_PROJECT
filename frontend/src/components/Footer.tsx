import { useNavigate } from 'react-router-dom'
import { Zap, Github, Linkedin, Twitter, Mail, MapPin, Phone } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export function Footer() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const footerBg = isDark ? 'bg-[#0F172A] border-white/10' : 'bg-white border-slate-200'
  const textMuted = isDark ? 'text-gray-400' : 'text-slate-600'
  const textHover = isDark ? 'hover:text-white' : 'hover:text-slate-900'
  const linkStyle = `${textMuted} ${textHover} transition-colors cursor-pointer`

  const currentYear = new Date().getFullYear()

  const handleAIChatClick = () => {
    const token = localStorage.getItem('token')
    if (token) {
      navigate('/dashboard')
    } else {
      navigate('/auth?mode=signin')
    }
  }

  return (
    <footer className={`border-t ${footerBg} transition-colors`}>
      <div className="container mx-auto px-6 py-16">
        <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-5">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <Zap className="h-6 w-6 text-white fill-white" />
              </div>
              <span className="text-2xl font-bold">FluxPricer</span>
            </div>
            <p className={`${textMuted} mb-6 max-w-sm leading-relaxed`}>
              AI-powered dynamic pricing platform that helps businesses optimize pricing strategies
              in real-time through natural language control and intelligent market analysis.
            </p>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className={linkStyle}
                aria-label="GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className={linkStyle}
                aria-label="LinkedIn"
              >
                <Linkedin className="h-5 w-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className={linkStyle}
                aria-label="Twitter"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a href="mailto:support@fluxpricer.com" className={linkStyle} aria-label="Email">
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Product Section */}
          <div>
            <h3 className="font-semibold mb-4 text-base">Product</h3>
            <ul className="space-y-3">
              <li>
                <span onClick={() => navigate('/')} className={linkStyle}>
                  Home
                </span>
              </li>
              <li>
                <span onClick={() => navigate('/pricing')} className={linkStyle}>
                  Pricing
                </span>
              </li>
              <li>
                <span onClick={handleAIChatClick} className={linkStyle}>
                  AI Chat
                </span>
              </li>
            </ul>
          </div>

          {/* Company Section */}
          <div>
            <h3 className="font-semibold mb-4 text-base">Company</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-2">
                <MapPin className={`h-5 w-5 ${textMuted} shrink-0`} />
                <div className={`text-sm ${textMuted}`}>
                  <p>123 Tech Avenue</p>
                  <p>San Francisco, CA 94102</p>
                  <p>United States</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Mail className={`h-5 w-5 ${textMuted}`} />
                <a href="mailto:support@fluxpricer.com" className={`text-sm ${linkStyle}`}>
                  support@fluxpricer.com
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className={`h-5 w-5 ${textMuted}`} />
                <a href="tel:+18005551234" className={`text-sm ${linkStyle}`}>
                  +1 (800) 555-1234
                </a>
              </div>
            </div>
          </div>

          {/* Resources Section */}
          <div>
            <h3 className="font-semibold mb-4 text-base">Resources</h3>
            <ul className="space-y-3">
              <li>
                <span onClick={() => navigate('/contact')} className={linkStyle}>
                  Contact Us
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div
          className={`mt-12 pt-8 border-t ${isDark ? 'border-white/10' : 'border-slate-200'} flex flex-col md:flex-row justify-between items-center gap-4`}
        >
          <p className={`text-sm ${textMuted}`}>
            &copy; {currentYear} FluxPricer. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <span className={`text-sm ${linkStyle}`}>Privacy Policy</span>
            <span className={`text-sm ${linkStyle}`}>Terms of Service</span>
            <span className={`text-sm ${linkStyle}`}>Cookie Policy</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
