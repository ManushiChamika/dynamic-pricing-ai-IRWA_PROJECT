import { Navigation } from '../components/Navigation'
import { Footer } from '../components/Footer'
import { ContactForm } from '../components/contact/ContactForm'
import { ContactInfoCards } from '../components/contact/ContactInfoCards'
import { FAQSection } from '../components/contact/FAQSection'
import { useTheme } from '../contexts/ThemeContext'
import { getPageThemeClasses } from '../lib/themeHelpers'

export function ContactPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const { pageClasses, heroGradient, dottedOverlay, secondarySurface, cardSurface, inputSurface } =
    getPageThemeClasses(isDark)

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
                className={`mb-12 text-xl md:text-2xl leading-relaxed max-w-3xl mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}
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
              <ContactForm inputSurface={inputSurface} isDark={isDark} />
              <ContactInfoCards theme={theme} cardSurface={cardSurface} />
            </div>
          </div>
        </section>

        <FAQSection theme={theme} />
      </main>

      <Footer />
    </div>
  )
}
