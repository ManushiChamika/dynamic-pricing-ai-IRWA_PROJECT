import { test, expect } from '@playwright/test'

test.describe('Responsive overlays', () => {
  test.describe('Mobile viewport', () => {
    test.use({ viewport: { width: 375, height: 812 } })

    test('both panels closed by default on mobile', async ({ page }) => {
      await page.goto('/auth')
      await page.fill('input[type="email"]', 'demo@example.com')
      await page.fill('input[type="password"]', '1234567890')
      await page.click('button[type="submit"]')
      await page.waitForURL(/.*chat/)

      const sidebar = page.locator('#sidebar')
      const pricesPanel = page.locator('#prices-panel')

      await expect(sidebar).toHaveClass(/-translate-x-full/)
      await expect(pricesPanel).toHaveClass(/translate-x-full/)
    })

    test('sidebar toggle opens sidebar with backdrop', async ({ page }) => {
      await page.goto('/auth')
      await page.fill('input[type="email"]', 'demo@example.com')
      await page.fill('input[type="password"]', '1234567890')
      await page.click('button[type="submit"]')
      await page.waitForURL(/.*chat/)

      await page.click('button[aria-label="Toggle sidebar"]')

      const sidebar = page.locator('#sidebar')
      const backdrop = page.locator('div[aria-hidden="true"].fixed.inset-0')

      await expect(sidebar).toHaveClass(/translate-x-0/)
      await expect(backdrop).toBeVisible()
    })

    test('backdrop click closes both panels', async ({ page }) => {
      await page.goto('/auth')
      await page.fill('input[type="email"]', 'demo@example.com')
      await page.fill('input[type="password"]', '1234567890')
      await page.click('button[type="submit"]')
      await page.waitForURL(/.*chat/)

      await page.click('button[aria-label="Toggle sidebar"]')
      await page.click('button[aria-label="Toggle prices panel"]')

      const backdrop = page.locator('div[aria-hidden="true"].fixed.inset-0')
      await backdrop.click()

      const sidebar = page.locator('#sidebar')
      const pricesPanel = page.locator('#prices-panel')

      await expect(sidebar).toHaveClass(/-translate-x-full/)
      await expect(pricesPanel).toHaveClass(/translate-x-full/)
    })

    test('Escape key closes both panels', async ({ page }) => {
      await page.goto('/auth')
      await page.fill('input[type="email"]', 'demo@example.com')
      await page.fill('input[type="password"]', '1234567890')
      await page.click('button[type="submit"]')
      await page.waitForURL(/.*chat/)

      await page.click('button[aria-label="Toggle sidebar"]')
      await page.click('button[aria-label="Toggle prices panel"]')

      await page.keyboard.press('Escape')

      const sidebar = page.locator('#sidebar')
      const pricesPanel = page.locator('#prices-panel')

      await expect(sidebar).toHaveClass(/-translate-x-full/)
      await expect(pricesPanel).toHaveClass(/translate-x-full/)
    })
  })

  test.describe('Desktop viewport', () => {
    test.use({ viewport: { width: 1200, height: 900 } })

    test('no backdrop on desktop; panels use push layout', async ({ page }) => {
      await page.goto('/auth')
      await page.fill('input[type="email"]', 'demo@example.com')
      await page.fill('input[type="password"]', '1234567890')
      await page.click('button[type="submit"]')
      await page.waitForURL(/.*chat/)

      const sidebar = page.locator('#sidebar')
      const pricesPanel = page.locator('#prices-panel')
      const backdrop = page.locator('div[aria-hidden="true"].fixed.inset-0')

      await expect(sidebar).toBeVisible()
      await expect(pricesPanel).toBeVisible()
      await expect(backdrop).not.toBeVisible()
    })
  })
})
