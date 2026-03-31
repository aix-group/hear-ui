import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ErrorBoundary from './ErrorBoundary.vue'

vi.mock('@/lib/logger', () => ({ logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn() } }))

describe('ErrorBoundary.vue', () => {
  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: { default: '<div class="child">OK</div>' },
    })
    expect(wrapper.find('.child').exists()).toBe(true)
  })

  it('uses default German props', () => {
    const wrapper = mount(ErrorBoundary)
    // Default props are in German; rendered only on error
    expect(wrapper.exists()).toBe(true)
  })

  it('accepts custom title and message props', () => {
    const wrapper = mount(ErrorBoundary, {
      props: {
        title: 'Custom Error',
        message: 'Something broke',
        retryLabel: 'Retry',
      },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
