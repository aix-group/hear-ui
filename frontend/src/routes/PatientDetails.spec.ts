import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import PatientDetails from './PatientDetails.vue'

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

describe('PatientDetails.vue', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: '1', name: 'Max Mustermann', input_features: {} }),
    }))
  })

  it('renders the component', async () => {
    const wrapper = await mountWithRouter(PatientDetails, {
      initialRoute: '/patient-detail/1',
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows back button with i18n key', async () => {
    const wrapper = await mountWithRouter(PatientDetails, {
      initialRoute: '/patient-detail/1',
    })
    expect(wrapper.html()).toContain('patient_details.back')
  })

  it('shows title i18n key', async () => {
    const wrapper = await mountWithRouter(PatientDetails, {
      initialRoute: '/patient-detail/1',
    })
    expect(wrapper.html()).toContain('patient_details.title')
  })

  it('shows action buttons', async () => {
    const wrapper = await mountWithRouter(PatientDetails, {
      initialRoute: '/patient-detail/1',
    })
    expect(wrapper.html()).toContain('patient_details.change_patient')
    expect(wrapper.html()).toContain('patient_details.delete_patient')
    expect(wrapper.html()).toContain('patient_details.generate_prediction')
  })
})
