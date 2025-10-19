import { useEffect, useRef, useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
  ScriptableContext,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

type PricePoint = { ts: number; price: number }

interface PriceChartProps {
  data: PricePoint[]
  sku: string
  theme?: 'light' | 'dark' | 'ocean' | 'forest' | 'sunset' | 'midnight' | 'rose'
}

export function PriceChart({ data, sku, theme = 'dark' }: PriceChartProps) {
  const chartRef = useRef<ChartJS<'line'>>(null)

  const isDark = theme !== 'light'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
  const textColor = isDark ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)'

  const prices = data.map((d) => d.price)
  const firstPrice = prices[0] || 0
  const lastPrice = prices[prices.length - 1] || 0
  const isUp = lastPrice >= firstPrice

  const lineColor = isUp ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'
  const gradientColor = isUp ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'

  const labels = data.map((d, i) => {
    const date = new Date(d.ts)
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return i % 5 === 0 || i === data.length - 1 ? `${minutes}:${seconds}` : ''
  })

  const chartData = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label: sku,
          data: prices,
          borderColor: lineColor,
          backgroundColor: (context: ScriptableContext<'line'>) => {
            const ctx = context.chart.ctx
            const gradient = ctx.createLinearGradient(0, 0, 0, context.chart.height)
            gradient.addColorStop(0, gradientColor)
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
            return gradient
          },
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: lineColor,
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          borderWidth: 2,
        },
      ],
    }),
    [labels, prices, sku, lineColor, gradientColor]
  )

  const options: ChartOptions<'line'> = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 750,
        easing: 'easeInOutQuart',
      },
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: true,
          backgroundColor: isDark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.9)',
          titleColor: textColor,
          bodyColor: textColor,
          borderColor: gridColor,
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: (context) => `$${context.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          display: true,
          grid: {
            display: true,
            color: gridColor,
            drawTicks: false,
          },
          ticks: {
            color: textColor,
            font: { size: 10 },
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 6,
          },
          border: {
            display: false,
          },
        },
        y: {
          display: true,
          position: 'right',
          grid: {
            display: true,
            color: gridColor,
            drawTicks: false,
          },
          ticks: {
            color: textColor,
            font: { size: 10 },
            callback: (value) => `$${Number(value).toFixed(0)}`,
            maxTicksLimit: 5,
          },
          border: {
            display: false,
          },
        },
      },
    }),
    [isDark, textColor, gridColor]
  )

  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return

    chart.data = chartData
    chart.options = options
    chart.update('none')
  }, [chartData, options])

  return (
    <div style={{ height: '180px', width: '100%', position: 'relative' }}>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  )
}
