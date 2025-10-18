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
