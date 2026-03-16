/**
 * Unit tests for the ModelCard component.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ModelCard from './ModelCard.vue'

const globalWithFetch = globalThis as typeof globalThis & { fetch: typeof fetch }

describe('ModelCard.vue', () => {
  beforeEach(() => {
    vi.spyOn(globalWithFetch, 'fetch').mockResolvedValue({
      ok: true,
      text: async () =>
        '## HEAR CI Prediction Model\n\n**Version:** v3.0\n\nModel description here.',
    } as Response)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('mounts without error', () => {
    const wrapper = mount(ModelCard)
    expect(wrapper.exists()).toBe(true)
  })

  it('displays loading state before data is fetched', () => {
    const wrapper = mount(ModelCard)
    // Initially modelCard is null
    expect(wrapper.vm.modelCard).toBeNull()
  })

  it('fetches model card data on created', async () => {
    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(globalWithFetch.fetch).toHaveBeenCalledOnce()
  })

  it('sets modelCard name to HEAR CI Prediction Model', async () => {
    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(wrapper.vm.modelCard?.name).toBe('HEAR CI Prediction Model')
  })

  it('extracts version from markdown', async () => {
    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(wrapper.vm.modelCard?.version).toBe('v3.0')
  })

  it('stores markdown text on modelCard', async () => {
    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(wrapper.vm.modelCard?.markdown).toContain('HEAR CI Prediction Model')
  })

  it('handles failed fetch gracefully', async () => {
    vi.restoreAllMocks()
    vi.spyOn(globalWithFetch, 'fetch').mockResolvedValue({
      ok: false,
      text: async () => '',
    } as Response)

    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(wrapper.vm.modelCard).toBeNull()
  })

  it('handles missing version in markdown', async () => {
    vi.restoreAllMocks()
    vi.spyOn(globalWithFetch, 'fetch').mockResolvedValue({
      ok: true,
      text: async () => '# Model Card\n\nNo version here.',
    } as Response)

    const wrapper = mount(ModelCard)
    await flushPromises()
    expect(wrapper.vm.modelCard).not.toBeNull()
    expect(wrapper.vm.modelCard?.version).toBe('')
  })

  it('renders card title after data loaded', async () => {
    const wrapper = mount(ModelCard)
    await flushPromises()
    await wrapper.vm.$nextTick()
    const title = wrapper.find('.v-card-title')
    expect(title.text()).toContain('HEAR CI Prediction Model')
  })
})
