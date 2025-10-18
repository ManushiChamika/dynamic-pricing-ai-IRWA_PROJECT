import { Navigation } from '../components/Navigation'
import { Footer } from '../components/Footer'
import { HeroSection } from '../components/landing/HeroSection'
import { FeaturesSection } from '../components/landing/FeaturesSection'
import { HowItWorksSection } from '../components/landing/HowItWorksSection'
import { CTASection } from '../components/landing/CTASection'
import { getPageThemeClasses, getSecondaryCta, getFeatureCardBase } from '../lib/themeHelpers'
import { useTheme } from '../contexts/ThemeContext'

export function LandingPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const { pageClasses, mutedText, softMutedText, heroGradient, dottedOverlay, secondarySurface } =
    getPageThemeClasses(isDark)
  const secondaryCta = getSecondaryCta(isDark)
  const featureCardBase = getFeatureCardBase(isDark)

  return (
    <div className={pageClasses}>
      <Navigation />

      <main className="pt-24">
        <HeroSection
          isDark={isDark}
          heroGradient={heroGradient}
          dottedOverlay={dottedOverlay}
          mutedText={mutedText}
          softMutedText={softMutedText}
          secondaryCta={secondaryCta}
        />

        <FeaturesSection
          isDark={isDark}
          mutedText={mutedText}
          secondarySurface={secondarySurface}
          featureCardBase={featureCardBase}
        />

        <HowItWorksSection isDark={isDark} mutedText={mutedText} />

        <CTASection isDark={isDark} mutedText={mutedText} />
      </main>

      <Footer />
    </div>
  )
}
