/**
 * Unit tests for the FeedbackForm component.
 */
import { describe, it, expect, vi, beforeEach, afterEach, type MockInstance } from 'vitest'

const globalWithFetch = globalThis as typeof globalThis & { fetch: typeof fetch }
import { mount } from '@vue/test-utils'
import FeedbackForm from './FeedbackForm.vue'

describe('FeedbackForm.vue', () => {
  const defaultProps = {
    predictionData: {
      prediction: 0.75,
      explanation: { age: 0.3, hearing_loss_duration: 0.2 },
    },
    patientData: {
      age: 45,
      hearing_loss_duration: 5,
      implant_type: 'type_b',
    },
  }

  let fetchSpy: MockInstance<Parameters<typeof fetch>, Promise<Response>>

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalWithFetch, 'fetch')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders agree and disagree buttons', () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const buttons = wrapper.findAll('.feedback-btn')
    expect(buttons.length).toBe(2)
    expect(buttons[0].text()).toContain('Zustimmen')
    expect(buttons[1].text()).toContain('Ablehnen')
  })

  it('renders a comment textarea', () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const textarea = wrapper.find('textarea')
    expect(textarea.exists()).toBe(true)
  })

  it('submit button is disabled when no choice is made', () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const submitBtn = wrapper.find('.submit-btn')
    expect(submitBtn.attributes('disabled')).toBeDefined()
  })

  it('submit button becomes enabled after clicking agree', async () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const agreeBtn = wrapper.find('.feedback-btn.agree')
    await agreeBtn.trigger('click')

    const submitBtn = wrapper.find('.submit-btn')
    expect(submitBtn.attributes('disabled')).toBeUndefined()
  })

  it('clicking agree highlights the agree button', async () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const agreeBtn = wrapper.find('.feedback-btn.agree')
    await agreeBtn.trigger('click')
    expect(agreeBtn.classes()).toContain('active')
  })

  it('clicking disagree highlights the disagree button', async () => {
    const wrapper = mount(FeedbackForm, { props: defaultProps })
    const disagreeBtn = wrapper.find('.feedback-btn.disagree')
    await disagreeBtn.trigger('click')
    expect(disagreeBtn.classes()).toContain('active')
  })

  it('submits feedback data on form submit', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    } as unknown as Response)

    const wrapper = mount(FeedbackForm, { props: defaultProps })

    // Select agree
    await wrapper.find('.feedback-btn.agree').trigger('click')

    // Type a comment
    await wrapper.find('textarea').setValue('Looks correct')

    // Submit form
    await wrapper.find('form').trigger('submit.prevent')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, options] = fetchSpy.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/v1/feedback/')
    expect(options.method).toBe('POST')

    const body = JSON.parse(options.body as string)
    expect(body.accepted).toBe(true)
    expect(body.comment).toBe('Looks correct')
    expect(body.prediction).toBe(0.75)
  })

  it('emits feedbackSubmitted on successful submit', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    } as unknown as Response)

    const wrapper = mount(FeedbackForm, { props: defaultProps })
    await wrapper.find('.feedback-btn.agree').trigger('click')
    await wrapper.find('form').trigger('submit.prevent')

    // Wait for async submit
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('feedbackSubmitted')).toBeTruthy()
  })

  it('shows error message on failed submit', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    } as unknown as Response)

    const wrapper = mount(FeedbackForm, { props: defaultProps })
    await wrapper.find('.feedback-btn.disagree').trigger('click')
    await wrapper.find('form').trigger('submit.prevent')

    // Wait for async
    await wrapper.vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-message').exists()).toBe(true)
  })
})
