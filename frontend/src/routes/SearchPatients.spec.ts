/**
 * Unit tests for the SearchPatients component.
 */
import { describe, it, expect, vi, beforeEach, afterEach, type MockInstance } from 'vitest'
import { mountWithRouter } from '../test/helpers'
import SearchPatients from './SearchPatients.vue'

const globalWithFetch = globalThis as typeof globalThis & { fetch: typeof fetch }

describe('SearchPatients.vue', () => {
  let fetchSpy: MockInstance<Parameters<typeof fetch>, Promise<Response>>

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalWithFetch, 'fetch')
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('renders the search input', async () => {
    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
  })

  it('has a "new patient" button linking to CreatePatient', async () => {
    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })
    const html = wrapper.html()
    expect(html).toContain('/create-patient')
  })

  it('fetches results after debounce when typing', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: '1', name: 'Max Mustermann' },
        { id: '2', name: 'Anna Schmidt' },
      ],
    } as unknown as Response)

    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })

    const input = wrapper.find('input')
    await input.setValue('Max')

    // Advance past debounce timer (200ms)
    await vi.advanceTimersByTimeAsync(300)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const callUrl = fetchSpy.mock.calls[0][0] as string
    expect(callUrl).toContain('/patients/search?q=Max')
  })

  it('displays search results as list items', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: '1', name: 'Max Mustermann' },
      ],
    } as unknown as Response)

    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })

    const input = wrapper.find('input')
    await input.setValue('Max')
    await vi.advanceTimersByTimeAsync(300)

    // Wait for Vue reactivity
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Max Mustermann')
  })

  it('clears results when search is emptied', async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => [{ id: '1', name: 'Max' }],
    } as unknown as Response)

    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })

    const input = wrapper.find('input')
    await input.setValue('Max')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    // Clear input
    await input.setValue('')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    // No fetch for empty input, results should be cleared
    expect(wrapper.findAll('.search-result-item').length).toBe(0)
  })

  it('handles network error gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    fetchSpy.mockRejectedValueOnce(new Error('Network error'))

    const wrapper = await mountWithRouter(SearchPatients, {
      initialRoute: '/search-patients',
    })

    const input = wrapper.find('input')
    await input.setValue('test')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    // Should not crash, results empty
    expect(wrapper.findAll('.search-result-item').length).toBe(0)
    consoleSpy.mockRestore()
  })
})
