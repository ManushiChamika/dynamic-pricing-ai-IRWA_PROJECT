export function getHowItWorksCard(
  color: 'indigo' | 'purple' | 'pink' | 'emerald',
  isDark: boolean
) {
  const palette: Record<
    typeof color,
    { card: string; hover: string; dot: string; shadow: string; hoverShadow: string }
  > = {
    indigo: {
      card: isDark ? 'from-indigo-500/5' : 'from-indigo-50',
      hover: isDark ? 'hover:border-indigo-500/50' : 'hover:border-indigo-500/40',
      dot: isDark ? 'from-indigo-500 to-indigo-600' : 'from-indigo-500 to-indigo-600',
      shadow: isDark ? 'shadow-indigo-500/25' : 'shadow-indigo-500/30',
      hoverShadow: isDark
        ? 'hover:shadow-lg hover:shadow-indigo-500/10'
        : 'hover:shadow-[0_24px_55px_rgba(79,70,229,0.15)]',
    },
    purple: {
      card: isDark ? 'from-purple-500/5' : 'from-purple-50',
      hover: isDark ? 'hover:border-purple-500/50' : 'hover:border-purple-500/40',
      dot: 'from-purple-500 to-purple-600',
      shadow: isDark ? 'shadow-purple-500/25' : 'shadow-purple-500/30',
      hoverShadow: isDark
        ? 'hover:shadow-lg hover:shadow-purple-500/10'
        : 'hover:shadow-[0_24px_55px_rgba(147,51,234,0.16)]',
    },
    pink: {
      card: isDark ? 'from-pink-500/5' : 'from-pink-50',
      hover: isDark ? 'hover:border-pink-500/50' : 'hover:border-pink-500/40',
      dot: 'from-pink-500 to-pink-600',
      shadow: isDark ? 'shadow-pink-500/25' : 'shadow-pink-500/30',
      hoverShadow: isDark
        ? 'hover:shadow-lg hover:shadow-pink-500/10'
        : 'hover:shadow-[0_24px_55px_rgba(236,72,153,0.14)]',
    },
    emerald: {
      card: isDark ? 'from-emerald-500/5' : 'from-emerald-50',
      hover: isDark ? 'hover:border-emerald-500/50' : 'hover:border-emerald-500/40',
      dot: 'from-emerald-500 to-emerald-600',
      shadow: isDark ? 'shadow-emerald-500/25' : 'shadow-emerald-500/30',
      hoverShadow: isDark
        ? 'hover:shadow-lg hover:shadow-emerald-500/10'
        : 'hover:shadow-[0_24px_55px_rgba(16,185,129,0.14)]',
    },
  }

  return palette[color]
}

export function getAuthThemeClasses(isDark: boolean) {
  return {
    labelColor: isDark ? 'text-gray-300' : 'text-slate-700',
    inputClass: isDark
      ? 'bg-gray-900 border-gray-600 text-white'
      : 'bg-white border-slate-300 text-slate-900 shadow-sm',
    switchLink: isDark
      ? 'text-indigo-300 hover:text-indigo-200'
      : 'text-indigo-600 hover:text-indigo-700',
    backLink: isDark ? 'text-gray-400 hover:text-gray-300' : 'text-slate-600 hover:text-slate-700',
  }
}

export function getPageThemeClasses(isDark: boolean) {
  return {
    pageClasses: isDark ? 'bg-[#0F172A] text-white' : 'bg-slate-50 text-slate-900',
    mutedText: isDark ? 'text-gray-400' : 'text-slate-700',
    softMutedText: isDark ? 'text-gray-500' : 'text-slate-600',
    helperText: isDark ? 'text-gray-500' : 'text-slate-600',
    heroGradient: isDark
      ? 'from-indigo-500/10 via-transparent to-purple-500/10'
      : 'from-indigo-400/15 via-transparent to-purple-300/10',
    dottedOverlay: isDark
      ? 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)'
      : 'radial-gradient(circle at 1px 1px, rgba(79,70,229,0.08) 1px, transparent 0)',
    secondarySurface: isDark ? 'bg-[#1E293B]/30' : 'bg-slate-100',
    cardSurface: isDark
      ? 'border-white/10 bg-[#1E293B]/50'
      : 'border-slate-200 bg-white shadow-[0_20px_45px_rgba(15,23,42,0.1)]',
    inputSurface: isDark
      ? 'bg-[#1E293B] border-white/20 text-white'
      : 'bg-white border-slate-300 text-slate-900',
  }
}

export function getFooterThemeClasses(isDark: boolean) {
  return {
    footerBg: isDark ? 'bg-[#0F172A] border-white/10' : 'bg-white border-slate-200',
    textMuted: isDark ? 'text-gray-400' : 'text-slate-600',
    textHover: isDark ? 'hover:text-white' : 'hover:text-slate-900',
  }
}

export function getSecondaryCta(isDark: boolean) {
  return isDark
    ? 'text-lg h-14 px-10 border border-white/20 text-white hover:bg-white/10 hover:border-white/40'
    : 'text-lg h-14 px-10 border border-slate-300 bg-white/85 text-slate-800 hover:bg-slate-100 hover:border-slate-400'
}

export function getFeatureCardBase(isDark: boolean) {
  return isDark
    ? 'relative rounded-2xl border border-white/10 bg-gradient-to-br'
    : 'relative rounded-2xl border border-slate-200 bg-white shadow-[0_18px_40px_rgba(15,23,42,0.12)]'
}

export function getPlanCardBase(isDark: boolean) {
  return isDark
    ? 'relative rounded-2xl border transition-all duration-300'
    : 'relative rounded-2xl border border-slate-200 bg-white shadow-[0_20px_45px_rgba(15,23,42,0.12)] transition-all duration-300'
}
