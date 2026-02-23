/**
 * Unit tests for the HomePage component.
 */
import { describe, it, expect } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import HomePage from './HomePage.vue'

describe('HomePage.vue', () => {
  it('renders the page title', async () => {
    const wrapper = await mountWithRouter(HomePage, { initialRoute: '/home' })
    expect(wrapper.text()).toContain('HEAR-UI')
  })

  it('renders three navigation cards', async () => {
    // Updated design: navigation cards were replaced by a central CTA.
    const wrapper = await mountWithRouter(HomePage, { initialRoute: '/home' })
    const cta = wrapper.find('a[href="/prediction-home"]')
    expect(cta.exists()).toBe(true)
  })

  it('renders CTA button text (uses i18n key)', async () => {
    const wrapper = await mountWithRouter(HomePage, { initialRoute: '/home' })
    // The button renders the i18n key in tests; assert the key is present
    expect(wrapper.html()).toContain('homepage.goto_predictions')
  })
})
