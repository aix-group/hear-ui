import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import PredictionsHome from './PredictionsHome.vue'

vi.mock('@/lib/api', () => ({ API_BASE: 'http://localhost:8000' }))
vi.mock('@/lib/logger', () => ({ logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

describe('PredictionsHome.vue', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({}),
    }))
  })

  it('renders the component', async () => {
    const wrapper = await mountWithRouter(PredictionsHome, {
      initialRoute: '/prediction-home',
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows page title i18n key', async () => {
    const wrapper = await mountWithRouter(PredictionsHome, {
      initialRoute: '/prediction-home',
    })
    expect(wrapper.html()).toContain('predictions_home.title')
  })

  it('shows search and create buttons', async () => {
    const wrapper = await mountWithRouter(PredictionsHome, {
      initialRoute: '/prediction-home',
    })
    expect(wrapper.html()).toContain('predictions_home.action_cards.search_patients.title')
    expect(wrapper.html()).toContain('predictions_home.action_cards.create_patient.title')
  })
})
