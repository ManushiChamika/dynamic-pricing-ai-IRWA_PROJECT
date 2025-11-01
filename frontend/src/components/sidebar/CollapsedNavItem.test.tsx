import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CollapsedNavItem } from './CollapsedNavItem'
import { Home } from 'lucide-react'

describe('CollapsedNavItem', () => {
  it('renders the icon and title as tooltip', () => {
    render(
      <CollapsedNavItem title="Home" isActive={false} onClick={() => {}}>
        <Home data-testid="icon" />
      </CollapsedNavItem>
    )

    const li = screen.getByRole('listitem')
    expect(li).toBeInTheDocument()
    expect(li).toHaveAttribute('title', 'Home')
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('applies active styles when isActive is true', () => {
    render(
      <CollapsedNavItem title="Home" isActive={true} onClick={() => {}}>
        <Home data-testid="icon2" />
      </CollapsedNavItem>
    )

    const li = screen.getByRole('listitem')
    expect(li).toHaveClass('bg-secondary')
  })
})
