import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('landing page should load', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('navigation').getByText('FluxPricer')).toBeVisible()
  })

  test('should navigate to auth page', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Get Started')
    await expect(page).toHaveURL(/.*auth/)
  })
})
