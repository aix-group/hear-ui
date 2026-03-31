import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PredictionGraph from '../components/PredictionGraph.vue'

describe('PredictionGraph.vue', () => {
  const baseProps = {
    predictionResult: 0.87,
    recommended: true,
    threshold: 0.5,
  }

  it('mounts and renders SVG', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('computes patient percentage correctly', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    expect(wrapper.text()).toContain('87%')
  })

  it('has WCAG role="img" on graph container', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    expect(wrapper.find('[role="img"]').exists()).toBe(true)
  })

  it('has aria-hidden on SVG element', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    expect(wrapper.find('svg').attributes('aria-hidden')).toBe('true')
  })

  it('renders graph path', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    const path = wrapper.find('.graph-curve')
    expect(path.exists()).toBe(true)
    expect(path.attributes('d')).toContain('M 0 96')
  })

  it('renders patient dot at correct x position', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    const circle = wrapper.find('.graph-patient-dot')
    expect(circle.attributes('cx')).toBe('87')
  })

  it('shows label-left class when recommended', () => {
    const wrapper = mount(PredictionGraph, { props: baseProps })
    expect(wrapper.find('.label-left').exists()).toBe(true)
  })

  it('shows label-right class when not recommended', () => {
    const wrapper = mount(PredictionGraph, {
      props: { ...baseProps, recommended: false },
    })
    expect(wrapper.find('.label-right').exists()).toBe(true)
  })

  it('handles null threshold', () => {
    const wrapper = mount(PredictionGraph, {
      props: { ...baseProps, threshold: null },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('handles 0% prediction', () => {
    const wrapper = mount(PredictionGraph, {
      props: { ...baseProps, predictionResult: 0 },
    })
    expect(wrapper.text()).toContain('0%')
  })

  it('handles 100% prediction', () => {
    const wrapper = mount(PredictionGraph, {
      props: { ...baseProps, predictionResult: 1 },
    })
    expect(wrapper.text()).toContain('100%')
  })
})
