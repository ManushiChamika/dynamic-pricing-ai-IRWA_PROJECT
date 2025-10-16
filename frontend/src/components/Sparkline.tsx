import React from 'react'
import { useSpring, animated } from '@react-spring/web'

export function Sparkline({ values, width = 120, height = 28 }: { values: number[]; width?: number; height?: number }) {
  const pad = 2
  const w = width
  const h = height

  const pathLength = useSpring({
    from: { strokeDashoffset: 200 },
    to: { strokeDashoffset: 0 },
    config: { duration: 800 }
  })

  if (!values.length) return <svg width={w} height={h} />
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = Math.max(1e-6, max - min)
  const step = (w - pad * 2) / Math.max(1, values.length - 1)
  const pts = values.map((v, i) => {
    const x = pad + i * step
    const y = h - pad - ((v - min) / range) * (h - pad * 2)
    return `${x},${y}`
  })
  const last = values[values.length - 1]
  const first = values[0]
  const up = last >= first

  return (
    <svg width={w} height={h}>
      <animated.polyline
        points={pts.join(' ')}
        fill="none"
        stroke={up ? '#10b981' : '#ef4444'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="200"
        style={pathLength}
      />
    </svg>
  )
}
