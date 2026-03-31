import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ExplanationChart from './ExplanationChart.vue'

vi.mock('plotly.js-dist-min', () => {
  return {
    newPlot: vi.fn(),
    purge: vi.fn(),
    react: vi.fn(),
  }
})

describe('ExplanationChart.vue', () => {
  const defaultProps = {
    matchedFeatures: [],
    featureLabels: ['Feature A', 'Feature B'],
    featureImportances: [0.3, -0.2],
    sectionBoundaries: [],
    language: 'en',
  }

  it('renders the component', () => {
    const wrapper = mount(ExplanationChart, { props: defaultProps })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows explanations title i18n key', () => {
    const wrapper = mount(ExplanationChart, { props: defaultProps })
    expect(wrapper.html()).toContain('prediction.explanations.title')
  })

  it('computes plot height based on feature count', () => {
    const wrapper = mount(ExplanationChart, { props: defaultProps })
    // 2 features * 40 + 80 = 160
    expect(wrapper.html()).toContain('160px')
  })

  it('renders with empty features', () => {
    const wrapper = mount(ExplanationChart, {
      props: { ...defaultProps, featureLabels: [], featureImportances: [] },
    })
    expect(wrapper.exists()).toBe(true)
    // Default height 320px for empty
    expect(wrapper.html()).toContain('320px')
  })
})
