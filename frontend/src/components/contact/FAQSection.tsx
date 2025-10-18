import React from 'react'
import { CONTACT_PAGE_FAQS } from '../../lib/contactPageConstants'

interface FAQ {
  question: string
  answer: string
}

export function FAQSection({ theme }: { theme: string }) {
  const isDark = theme === 'dark'

  return (
    <section className={`px-6 py-24 ${isDark ? 'bg-[#1E293B]/30' : 'bg-gray-50'}`}>
      <div className="container mx-auto max-w-4xl">
        <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>

        <div
          className={`rounded-2xl border ${isDark ? 'border-white/10 bg-[#1E293B]/50' : 'border-gray-200 bg-white'} p-8`}
        >
          <div className="space-y-8">
            {CONTACT_PAGE_FAQS.map((faq: FAQ, index: number) => (
              <div key={index}>
                <h3 className="text-lg font-semibold mb-2">{faq.question}</h3>
                <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
