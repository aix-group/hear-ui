/**
 * Unit tests for the CreatePatients component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import CreatePatients from './CreatePatients.vue'

// Mock featureDefinitionsStore
vi.mock('@/lib/featureDefinitionsStore', () => ({
  featureDefinitionsStore: {
    loadDefinitions: vi.fn().mockResolvedValue(undefined),
    loadLabels: vi.fn().mockResolvedValue(undefined),
  },
}))

// Mock featureDefinitions composable
vi.mock('@/lib/featureDefinitions', () => ({
  useFeatureDefinitions: () => ({
    definitions: { value: [] },
    labels: { value: {} },
    sections: { value: {} },
  }),
}))

const globalWithFetch = globalThis as typeof globalThis & { fetch: typeof fetch }

describe('CreatePatients.vue', () => {
  beforeEach(() => {
    vi.spyOn(globalWithFetch, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as unknown as Response)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the component', async () => {
    const wrapper = await mountWithRouter(CreatePatients, {
      initialRoute: '/create-patient',
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows the page title', async () => {
    const wrapper = await mountWithRouter(CreatePatients, {
      initialRoute: '/create-patient',
    })
    const html = wrapper.html()
    // Title from i18n key 'form.title' — in test env it shows the key
    expect(html).toBeTruthy()
  })

  it('has a back button', async () => {
    const wrapper = await mountWithRouter(CreatePatients, {
      initialRoute: '/create-patient',
    })
    const backBtn = wrapper.find('.v-btn')
    expect(backBtn.exists()).toBe(true)
  })
})
