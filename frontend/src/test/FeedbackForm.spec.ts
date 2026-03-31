import { describe, it, expect, vi} from 'vitest'
import { mount } from '@vue/test-utils'
import FeedbackForm from '../components/FeedbackForm.vue'

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const baseProps = {
  predictionData: {
    prediction: 0.87,
    explanation: { feature_a: 0.3, feature_b: -0.1 },
  },
  patientData: {
    age: 55,
    hearing_loss_duration: 10,
    implant_type: 'CI',
  },
}

describe('FeedbackForm.vue', () => {
  it('mounts without error', () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders agree and disagree buttons', () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    const buttons = wrapper.findAll('.feedback-btn')
    expect(buttons.length).toBe(2)
  })

  it('agree button has aria-pressed attribute', () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    const agreeBtn = wrapper.find('.feedback-btn.agree')
    expect(agreeBtn.attributes('aria-pressed')).toBe('false')
  })

  it('sets aria-pressed=true on agree click', async () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    const agreeBtn = wrapper.find('.feedback-btn.agree')
    await agreeBtn.trigger('click')
    expect(agreeBtn.attributes('aria-pressed')).toBe('true')
  })

  it('submit button is disabled when no selection', () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    const submitBtn = wrapper.find('.submit-btn')
    expect(submitBtn.attributes('disabled')).toBeDefined()
  })

  it('submit button is enabled after selection', async () => {
    const wrapper = mount(FeedbackForm, { props: baseProps })
    await wrapper.find('.feedback-btn.agree').trigger('click')
    const submitBtn = wrapper.find('.submit-btn')
    expect(submitBtn.attributes('disabled')).toBeUndefined()
  })

  it('error message has role=alert', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    const wrapper = mount(FeedbackForm, { props: baseProps })
    await wrapper.find('.feedback-btn.agree').trigger('click')
    await wrapper.find('form').trigger('submit')
    // Wait for async
    await vi.waitFor(() => {
      expect(wrapper.find('[role="alert"]').exists()).toBe(true)
    })
  })
})
