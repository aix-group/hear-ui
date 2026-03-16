/**
 * Unit tests for the FeedbackDialog component.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FeedbackDialog, { type FeedbackData } from './FeedbackDialog.vue'

describe('FeedbackDialog.vue', () => {
  it('mounts without error', () => {
    const wrapper = mount(FeedbackDialog)
    expect(wrapper.exists()).toBe(true)
  })

  it('dialog is closed by default', () => {
    const wrapper = mount(FeedbackDialog)
    expect(wrapper.vm.dialog).toBe(false)
  })

  it('open() sets dialog to true', () => {
    const wrapper = mount(FeedbackDialog)
    wrapper.vm.open()
    expect(wrapper.vm.dialog).toBe(true)
  })

  it('close() sets dialog to false', () => {
    const wrapper = mount(FeedbackDialog)
    wrapper.vm.open()
    expect(wrapper.vm.dialog).toBe(true)
    wrapper.vm.close()
    expect(wrapper.vm.dialog).toBe(false)
  })

  it('FeedbackData interface can be used as type', () => {
    const feedbackData: FeedbackData = {
      modelPrediction: 0.85,
      userAssessment: 1,
      comments: 'Looks correct',
      timestamp: new Date(),
      patientId: 'patient-123',
      clinicianId: 'clinician-456',
    }
    expect(feedbackData.modelPrediction).toBe(0.85)
    expect(feedbackData.userAssessment).toBe(1)
    expect(feedbackData.comments).toBe('Looks correct')
    expect(feedbackData.patientId).toBe('patient-123')
    expect(feedbackData.clinicianId).toBe('clinician-456')
    expect(feedbackData.timestamp).toBeInstanceOf(Date)
  })

  it('renders a v-dialog element in DOM', () => {
    const wrapper = mount(FeedbackDialog, { attachTo: document.body })
    // v-dialog is in the component template even when dialog=false
    const dialog = wrapper.findComponent({ name: 'VDialog' })
    expect(dialog.exists()).toBe(true)
    wrapper.unmount()
  })
})
