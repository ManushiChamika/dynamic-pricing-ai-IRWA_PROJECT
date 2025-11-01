import React from 'react'
import { Mail, Phone, MapPin } from 'lucide-react'

function ContactInfoCardsComponent({ theme, cardSurface }: { theme: string; cardSurface: string }) {
  const isDark = theme === 'dark'

  return (
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
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
            <p className={isDark ? 'text-gray-300' : 'text-gray-700'}>
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
          <ul className={`space-y-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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
  )
}

export const ContactInfoCards = React.memo(ContactInfoCardsComponent)
