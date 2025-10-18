import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/button'
import { ArrowRight, MessageSquare } from 'lucide-react'
import { useAuthUser } from '../../stores/authStore'

interface CTASectionProps {
  isDark: boolean
  mutedText: string
}

export function CTASection({ isDark, mutedText }: CTASectionProps) {
  const navigate = useNavigate()
  const user = useAuthUser()

  return (
    <section
      className={`px-6 py-24 bg-gradient-to-br ${
        isDark
          ? 'from-indigo-500/10 via-purple-500/10 to-pink-500/10'
          : 'from-indigo-100 via-purple-100 to-pink-100'
      }`}
    >
      <div className="container mx-auto max-w-4xl text-center">
        <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Pricing?</h2>
        <p className={`text-xl ${mutedText} mb-10 max-w-2xl mx-auto text-center`}>
          Join businesses using AI to stay competitive and maximize revenue
        </p>
        {user ? (
          <Button
            className="text-lg h-16 px-12 leading-none bg-gradient-to-r from-indigo-500 to-purple-600 text-white border border-transparent shadow-lg shadow-indigo-500/25"
            onClick={() => navigate('/chat')}
          >
            Go to Chat
            <MessageSquare className="ml-2 h-5 w-5" />
          </Button>
        ) : (
          <>
            <Button
              className="text-lg h-16 px-12 leading-none bg-gradient-to-r from-indigo-500 to-purple-600 text-white border border-transparent shadow-lg shadow-indigo-500/25"
              onClick={() => navigate('/auth?mode=signup')}
            >
              Get Started Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <p className="mt-6 text-sm text-gray-500">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </>
        )}
      </div>
    </section>
  )
}
