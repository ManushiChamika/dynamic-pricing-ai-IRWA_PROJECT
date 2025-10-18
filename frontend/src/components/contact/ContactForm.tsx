import React, { useState } from 'react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Textarea } from '../ui/textarea'
import { ArrowRight } from 'lucide-react'

interface FormData {
  name: string
  email: string
  company: string
  message: string
}

export function ContactForm({
  inputSurface,
  isDark,
}: {
  inputSurface: string
  isDark: boolean
}) {
  const [formData, setFormData] = useState<FormData>({
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

    setTimeout(() => {
      setSubmitted(true)
      setLoading(false)
      setFormData({ name: '', email: '', company: '', message: '' })

      setTimeout(() => setSubmitted(false), 5000)
    }, 1500)
  }

  return (
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
  )
}
