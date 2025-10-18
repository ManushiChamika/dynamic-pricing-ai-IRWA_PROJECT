import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { Navigation } from '../components/Navigation'
import { Footer } from '../components/Footer'
import { ArrowRight, Mail, MapPin, Phone } from 'lucide-react'
import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'

export function ContactPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const pageClasses = isDark ? 'bg-[#0F172A] text-white' : 'bg-slate-50 text-slate-900'
  const mutedText = isDark ? 'text-gray-400' : 'text-slate-700'
  const heroGradient = isDark
    ? 'from-indigo-500/10 via-transparent to-purple-500/10'
    : 'from-indigo-400/15 via-transparent to-purple-300/10'
  const dottedOverlay = isDark
    ? 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)'
    : 'radial-gradient(circle at 1px 1px, rgba(79,70,229,0.08) 1px, transparent 0)'
  const secondarySurface = isDark ? 'bg-[#1E293B]/30' : 'bg-slate-100'
  const cardSurface = isDark
    ? 'border-white/10 bg-[#1E293B]/50'
    : 'border-slate-200 bg-white shadow-[0_20px_45px_rgba(15,23,42,0.1)]'
  const inputSurface = isDark
    ? 'bg-[#1E293B] border-white/20 text-white'
    : 'bg-white border-slate-300 text-slate-900'
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    // Simulate sending form
    setTimeout(() => {
      setSubmitted(true)
      setLoading(false)
      setFormData({ name: '', email: '', company: '', message: '' })

      // Reset after 5 seconds
      setTimeout(() => setSubmitted(false), 5000)
    }, 1500)
  }

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
                Get in{' '}
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Touch
                </span>
              </h1>

              <p
                className={`mb-12 text-xl md:text-2xl leading-relaxed max-w-3xl mx-auto ${mutedText}`}
              >
                Have questions? We&apos;re here to help. Reach out to our team and we&apos;ll get
                back to you as soon as possible.
              </p>
            </div>
          </div>
        </section>

        <section className={`px-6 py-24 ${secondarySurface}`}>
          <div className="container mx-auto max-w-6xl">
            <div className="grid gap-12 md:grid-cols-2">
              {/* Contact Form */}
              <div>
                <h2 className="text-3xl font-bold mb-8">Send us a Message</h2>

                {submitted && (
                  <div
                    className={`mb-6 p-4 rounded-lg border ${
                      isDark
                        ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-200'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                    }`}
                  >
                    ✓ Thank you! We&apos;ve received your message and will be in touch soon.
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Name</label>
                    <Input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Your name"
                      required
                      className={inputSurface}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Email</label>
                    <Input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="your@email.com"
                      required
                      className={inputSurface}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Company</label>
                    <Input
                      type="text"
                      name="company"
                      value={formData.company}
                      onChange={handleChange}
                      placeholder="Your company"
                      className={inputSurface}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Message</label>
                    <Textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Tell us how we can help..."
                      rows={6}
                      required
                      className={`${inputSurface} min-h-[160px]`}
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full h-12 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0"
                  >
                    {loading ? 'Sending...' : 'Send Message'}
                    {!loading && <ArrowRight className="ml-2 h-5 w-5" />}
                  </Button>
                </form>
              </div>

              {/* Contact Information */}
              <div>
                <h2 className="text-3xl font-bold mb-8">Contact Information</h2>

                <div className="space-y-8">
                  <div className="flex gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex-shrink-0">
                      <Mail className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Email</h3>
                      <a
                        href="mailto:support@fluxpricer.com"
                        className="text-indigo-400 hover:text-indigo-300 transition-colors"
                      >
                        support@fluxpricer.com
                      </a>
                      <p
                        className={`text-sm mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}
                      >
                        We typically respond within 24 hours
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex-shrink-0">
                      <Phone className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Phone</h3>
                      <a
                        href="tel:+18005551234"
                        className="text-purple-400 hover:text-purple-300 transition-colors"
                      >
                        +1 (800) 555-1234
                      </a>
                      <p
                        className={`text-sm mt-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}
                      >
                        Monday – Friday, 9 AM – 6 PM EST
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex-shrink-0">
                      <MapPin className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Address</h3>
                      <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                        123 Tech Avenue
                        <br />
                        San Francisco, CA 94102
                        <br />
                        United States
                      </p>
                    </div>
                  </div>

                  <div className={`rounded-2xl border ${cardSurface} p-6 mt-8`}>
                    <h3 className="font-semibold mb-4">Response Times</h3>
                    <ul
                      className={`space-y-3 text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}
                    >
                      <li className="flex justify-between">
                        <span>Emails:</span>
                        <span className="font-medium">24 hours</span>
                      </li>
                      <li className="flex justify-between">
                        <span>Live Chat:</span>
                        <span className="font-medium">Within 2 hours</span>
                      </li>
                      <li className="flex justify-between">
                        <span>Phone Support:</span>
                        <span className="font-medium">Within 1 hour</span>
                      </li>
                      <li className="flex justify-between">
                        <span>Enterprise Support:</span>
                        <span className="font-medium">24/7</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={`px-6 py-24 ${theme === 'dark' ? 'bg-[#1E293B]/30' : 'bg-gray-50'}`}>
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>

            <div
              className={`rounded-2xl border ${theme === 'dark' ? 'border-white/10 bg-[#1E293B]/50' : 'border-gray-200 bg-white'} p-8`}
            >
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-semibold mb-2">How quickly can I get started?</h3>
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    You can sign up and be running your first AI pricing analysis within minutes. No
                    setup or technical knowledge required.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">
                    Do you offer onboarding assistance?
                  </h3>
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    Yes! All plans include access to our documentation and video tutorials.
                    Professional and Enterprise plans include dedicated onboarding.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">What integrations do you support?</h3>
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    We support all major ecommerce platforms (Shopify, WooCommerce, Magento),
                    analytics tools, and have a REST API for custom integrations.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Is my data secure?</h3>
                  <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                    Absolutely. We use enterprise-grade encryption, SOC 2 compliance, and regular
                    security audits to protect your data.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
