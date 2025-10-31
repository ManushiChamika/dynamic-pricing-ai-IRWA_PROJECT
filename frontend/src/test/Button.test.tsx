import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../components/ui/button'

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('handles disabled state', () => {
    render(<Button disabled>Disabled</Button>)
    const button = screen.getByText('Disabled')
    expect(button).toBeDisabled()
  })

  it('responds to clicks', async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Press</Button>)
    const button = screen.getByText('Press')
    await userEvent.click(button)
    expect(handleClick).toHaveBeenCalled()
  })
})
