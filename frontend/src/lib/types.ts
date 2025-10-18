export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  model?: string
  thinking?: string
  agents?: string[]
  activeAgents?: string[]
  tools?: string[]
  metadata?: {
    tokens?: number
    cost?: number
    apiCalls?: number
  }
}

export interface Thread {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export interface Settings {
  theme: 'light' | 'dark'
  showModel: boolean
  showTimestamps: boolean
  showMeta: boolean
  showThinking: boolean
  mode: 'user' | 'developer'
  streaming: 'sse' | 'none'
}

export interface PriceData {
  productId: string
  productName: string
  currentPrice: number
  recommendedPrice: number
  competitorPrices: { source: string; price: number }[]
  timestamp: Date
}
