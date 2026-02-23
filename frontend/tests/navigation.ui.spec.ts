/**
 * E2E Tests: Navigation & Core Pages
 *
 * Tests that the SPA loads correctly and navigation between pages works.
 * Matches playwright config `chromium` project pattern (*.ui.spec.ts).
 */
import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('home page loads and shows title', async ({ page }) => {
    await page.goto('/home')
    // Wait for Vuetify to render
    await expect(page.locator('#hear-ui')).toBeVisible()
    // The app should show the HEAR-UI branding
    await expect(page.locator('body')).toContainText('HEAR')
  })

  test('redirects / to /home', async ({ page }) => {
    await page.goto('/')
    await page.waitForURL('**/home')
    expect(page.url()).toContain('/home')
  })

  test('home page has CTA button to predictions', async ({ page }) => {
    await page.goto('/home')
    // Home page was redesigned: uses a CTA button instead of navigation cards
    const ctaBtn = page.locator('a.v-btn, .v-btn').filter({ hasText: /Predictions|Vorhersage/i })
    await expect(ctaBtn.first()).toBeVisible()
  })

  test('CTA button navigates to prediction-home', async ({ page }) => {
    await page.goto('/home')
    // Click the main CTA button that links to PredictionsHome
    const ctaBtn = page.locator('.v-btn').filter({ hasText: /Predictions|Vorhersage/i })
    await ctaBtn.first().click()
    await page.waitForURL('**/prediction-home')
    expect(page.url()).toContain('/prediction-home')
  })

  test('sidebar navigation works', async ({ page }) => {
    await page.goto('/home')
    // Open the drawer via the hamburger menu
    const navIcon = page.locator('.v-app-bar-nav-icon')
    await navIcon.click()

    // Click "Search Patients" nav item
    const searchNav = page.locator('.nav-item').nth(1)
    await searchNav.click()
    await page.waitForURL('**/search-patients')
    expect(page.url()).toContain('/search-patients')
  })

  test('unknown route shows 404 page', async ({ page }) => {
    await page.goto('/does-not-exist-at-all')
    await expect(page.locator('body')).toContainText('404')
  })

  test('404 page has go home button', async ({ page }) => {
    await page.goto('/does-not-exist-at-all')
    const homeBtn = page.locator('button', { hasText: /Startseite|Home/i })
    await expect(homeBtn).toBeVisible()
  })

  test('language switcher is visible in app bar', async ({ page }) => {
    await page.goto('/home')
    const langBtn = page.locator('.language-button')
    await expect(langBtn).toBeVisible()
  })

  test('language switcher toggles language', async ({ page }) => {
    await page.goto('/home')
    const langBtn = page.locator('.language-button')

    // Get initial text
    const initialText = await langBtn.textContent()

    // Click to switch
    await langBtn.click()
    await page.waitForTimeout(500)

    const newText = await langBtn.textContent()
    expect(newText).not.toBe(initialText)
  })
})
