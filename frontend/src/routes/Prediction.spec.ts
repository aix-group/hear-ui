import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import Prediction from './Prediction.vue'

vi.mock('@/lib/api', () => ({ API_BASE: 'http://localhost:8000' }))
vi.mock('@/lib/logger', () => ({ logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))
vi.mock('@/lib/featureDefinitions', () => ({
  useFeatureDefinitions: () => ({
    definitions: { value: [] },
    labels: { value: {} },
    sections: { value: {} },
    sectionOrder: { value: [] },
  }),
}))
vi.mock('@/lib/featureDefinitionsStore', () => ({
  featureDefinitionsStore: { loadLabels: vi.fn().mockResolvedValue(undefined), loadDefinitions: vi.fn().mockResolvedValue(undefined) },
}))
vi.mock('plotly.js-dist-min', () => ({
  newPlot: vi.fn(),
  purge: vi.fn(),
}))

describe('Prediction.vue', () => {
  beforeEach(() => {
    vi.stubGlobal('scrollTo', vi.fn())
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        prediction: 0.75,
        threshold: 0.5,
        recommended: true,
        matched_features: [],
        feature_labels: [],
        feature_importances: [],
        section_boundaries: [],
        warnings: [],
      }),
    }))
  })

  it('renders the component', async () => {
    const wrapper = await mountWithRouter(Prediction, {
      initialRoute: '/prediction/1',
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows prediction title', async () => {
    const wrapper = await mountWithRouter(Prediction, {
      initialRoute: '/prediction/1',
    })
    expect(wrapper.text()).toContain('Vorhersage für')
  })
})
