import React from 'react'
import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { ChatHeader } from './ChatHeader'
import { BrowserRouter } from 'react-router-dom'
import { useSidebar } from '../../stores/sidebarStore'
import { usePanels } from '../../stores/panelsStore'
import { beforeEach, describe, it, expect, vi } from 'vitest'

vi.mock('../../hooks/useProducts', () => ({
  useProducts: () => ({ products: [] }),
}))

vi.mock('../../hooks/useIncidents', () => ({
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

describe('ChatHeader accessibility', () => {
  beforeEach(() => {
    localStorage.clear()
    useSidebar.getState().setCollapsed(true)
    usePanels.getState().setPricesCollapsed(true)
  })

  it('sidebar toggle has aria-expanded reflecting state', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <ChatHeader />
      </BrowserRouter>
    )

    const sidebarToggle = screen.getByLabelText('Toggle sidebar')
    expect(sidebarToggle).toHaveAttribute('aria-expanded', 'false')
    expect(sidebarToggle).toHaveAttribute('aria-controls', 'sidebar')

    await user.click(sidebarToggle)
    expect(sidebarToggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('prices toggle has aria-expanded reflecting state', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <ChatHeader />
      </BrowserRouter>
    )

    const pricesToggle = screen.getByLabelText('Toggle prices panel')
    expect(pricesToggle).toHaveAttribute('aria-expanded', 'false')
    expect(pricesToggle).toHaveAttribute('aria-controls', 'prices-panel')

    await user.click(pricesToggle)
    expect(pricesToggle).toHaveAttribute('aria-expanded', 'true')
  })
})
