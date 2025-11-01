import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useProducts } from '../hooks/useProducts'
import React from 'react'

vi.mock('../stores/authStore', () => ({
  useAuthToken: () => 'demo-token',
}))

function TestComponent() {
  const { products } = useProducts()
  return (
    <div>
      {products.map((p) => (
        <div key={p} data-testid="sku">
          {p}
        </div>
      ))}
    </div>
  )
}

describe('useProducts hook', () => {
  beforeAll(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ products: [{ sku: 'SKU123' }] }),
        })
      )
    )
  })

  afterAll(() => {
    vi.restoreAllMocks()
  })

  it('fetches and renders product SKUs from the API', async () => {
    render(<TestComponent />)

    const sku = await screen.findByTestId('sku')
    expect(sku).toBeTruthy()
  })
})
