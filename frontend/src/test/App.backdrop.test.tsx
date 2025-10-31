import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { BrowserRouter } from 'react-router-dom'
import App from '../App'
import { useSidebar } from '../stores/sidebarStore'
import { usePanels } from '../stores/panelsStore'
import { beforeEach, describe, it, expect, vi } from 'vitest'

vi.mock('../hooks/useProducts', () => ({
  useProducts: () => ({ products: [] }),
}))

vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ incidents: [], acknowledgeIncident: vi.fn(), resolveIncident: vi.fn() }),
}))

vi.mock('../../hooks/usePriceStream', () => ({
  usePriceStream: () => ({}),
}))

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('max-width: 767px'),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

describe('App backdrop behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    useSidebar.getState().setCollapsed(true)
    usePanels.getState().setPricesCollapsed(true)
  })

  it('shows backdrop when sidebar is open on mobile', () => {
    useSidebar.getState().setCollapsed(false)
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    const backdrop = document.querySelector('div[aria-hidden="true"].fixed.inset-0')
    expect(backdrop).toBeInTheDocument()
    expect(backdrop).toHaveClass('bg-black/40')
  })

  it('shows backdrop when prices panel is open on mobile', () => {
    usePanels.getState().setPricesCollapsed(false)
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    const backdrop = document.querySelector('div[aria-hidden="true"].fixed.inset-0')
    expect(backdrop).toBeInTheDocument()
  })

  it('hides backdrop when both panels are closed', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    const backdrop = document.querySelector('div[aria-hidden="true"].fixed.inset-0')
    expect(backdrop).not.toBeInTheDocument()
  })

  it('clicking backdrop closes both panels', () => {
    useSidebar.getState().setCollapsed(false)
    usePanels.getState().setPricesCollapsed(false)

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    const backdrop = document.querySelector('div[aria-hidden="true"].fixed.inset-0')
    expect(backdrop).toBeInTheDocument()

    fireEvent.click(backdrop!)

    expect(useSidebar.getState().collapsed).toBe(true)
    expect(usePanels.getState().pricesCollapsed).toBe(true)
  })

  it('pressing Escape closes both panels', () => {
    useSidebar.getState().setCollapsed(false)
    usePanels.getState().setPricesCollapsed(false)

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    fireEvent.keyDown(window, { key: 'Escape' })

    expect(useSidebar.getState().collapsed).toBe(true)
    expect(usePanels.getState().pricesCollapsed).toBe(true)
  })
})
