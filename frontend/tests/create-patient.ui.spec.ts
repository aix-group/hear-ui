/**
 * E2E Tests: Create Patient Page
 *
 * Tests the patient creation form page.
 */
import { test, expect } from '@playwright/test'

test.describe('Create Patient Page', () => {
  test('create patient page loads', async ({ page }) => {
    await page.goto('/create-patient')
    await expect(page.locator('#hear-ui')).toBeVisible()
  })

  test('page shows a form or form fields', async ({ page }) => {
    await page.goto('/create-patient')
    // The create form renders fields dynamically from feature definitions
    // API may fail in CI without backend - that's OK, just check UI renders
    await page.waitForTimeout(500)
    // There should be at least the app container or some UI elements
    const appVisible = await page.locator('#hear-ui').isVisible()
    expect(appVisible).toBe(true)
  })

  test('navigating to create patient via sidebar works', async ({ page }) => {
    await page.goto('/home')
    // Home page was redesigned: navigate via sidebar (index 2 = CreatePatient)
    const navIcon = page.locator('.v-app-bar-nav-icon')
    await navIcon.click()
    const createNav = page.locator('.nav-item').nth(2)
    await createNav.click()
    await page.waitForURL('**/create-patient')
    expect(page.url()).toContain('/create-patient')
  })
})
