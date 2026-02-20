/**
 * Unit tests for the featureDefinitionsStore reactive store.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { featureDefinitionsStore } from '@/lib/featureDefinitionsStore'

describe('featureDefinitionsStore', () => {
  let fetchSpy: ReturnType<typeof vi.spyOn<typeof globalThis, 'fetch'>>

  beforeEach(() => {
    // Reset store state
    featureDefinitionsStore.definitions.value = []
    featureDefinitionsStore.labels.value = {}
    featureDefinitionsStore.sections.value = {}
    featureDefinitionsStore.sectionOrder.value = []
    featureDefinitionsStore.error.value = null
    featureDefinitionsStore.loading.value = false

    fetchSpy = vi.spyOn(globalThis, 'fetch')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('loadDefinitions', () => {
    it('populates definitions from API response', async () => {
      const mockFeatures = [
        { raw: 'Alter [J]', normalized: 'age', type: 'numeric' },
        { raw: 'Geschlecht', normalized: 'gender', type: 'categorical' },
      ]

      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ features: mockFeatures, section_order: ['demographics'] }),
      } as unknown as Response)

      await featureDefinitionsStore.loadDefinitions()

      expect(featureDefinitionsStore.definitions.value).toHaveLength(2)
      expect(featureDefinitionsStore.definitions.value[0].raw).toBe('Alter [J]')
      expect(featureDefinitionsStore.sectionOrder.value).toEqual(['demographics'])
      expect(featureDefinitionsStore.error.value).toBeNull()
    })

    it('handles network error gracefully', async () => {
      fetchSpy.mockRejectedValueOnce(new Error('Network failure'))

      await featureDefinitionsStore.loadDefinitions()

      expect(featureDefinitionsStore.definitions.value).toEqual([])
      expect(featureDefinitionsStore.error.value).toBe('Network failure')
    })

    it('handles non-JSON response', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'text/html' }),
        text: async () => '<html>Not JSON</html>',
      } as unknown as Response)

      await featureDefinitionsStore.loadDefinitions()

      expect(featureDefinitionsStore.definitions.value).toEqual([])
      expect(featureDefinitionsStore.error.value).toBeTruthy()
    })

    it('handles non-ok response', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: false,
        status: 500,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: async () => 'Server Error',
      } as unknown as Response)

      await featureDefinitionsStore.loadDefinitions()

      expect(featureDefinitionsStore.definitions.value).toEqual([])
      expect(featureDefinitionsStore.error.value).toBe('Server Error')
    })

    it('sets loading state during fetch', async () => {
      let resolvePromise: (v: unknown) => void
      const pending = new Promise((resolve) => { resolvePromise = resolve })

      fetchSpy.mockReturnValueOnce(pending as Promise<Response>)

      const loadPromise = featureDefinitionsStore.loadDefinitions()
      expect(featureDefinitionsStore.loading.value).toBe(true)

      resolvePromise!({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ features: [] }),
      })

      await loadPromise
      expect(featureDefinitionsStore.loading.value).toBe(false)
    })
  })

  describe('loadLabels', () => {
    it('populates labels from API response', async () => {
      fetchSpy.mockResolvedValueOnce({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          labels: { age: 'Alter', gender: 'Geschlecht' },
          sections: { demographics: 'Demographie' },
        }),
      } as unknown as Response)

      await featureDefinitionsStore.loadLabels('de')

      expect(featureDefinitionsStore.labels.value).toEqual({
        age: 'Alter',
        gender: 'Geschlecht',
      })
      expect(featureDefinitionsStore.sections.value).toEqual({
        demographics: 'Demographie',
      })
      expect(featureDefinitionsStore.error.value).toBeNull()
    })

    it('handles error in label loading', async () => {
      fetchSpy.mockRejectedValueOnce(new Error('Label fetch failed'))

      await featureDefinitionsStore.loadLabels('de')

      expect(featureDefinitionsStore.labels.value).toEqual({})
      expect(featureDefinitionsStore.error.value).toBe('Label fetch failed')
    })
  })

  describe('definitionsByNormalized', () => {
    it('creates lookup map by normalized key', () => {
      featureDefinitionsStore.definitions.value = [
        { raw: 'Alter [J]', normalized: 'age' },
        { raw: 'Geschlecht', normalized: 'gender' },
      ]

      const map = featureDefinitionsStore.definitionsByNormalized.value
      expect(map['age'].raw).toBe('Alter [J]')
      expect(map['gender'].raw).toBe('Geschlecht')
    })

    it('skips entries without normalized key', () => {
      featureDefinitionsStore.definitions.value = [
        { raw: 'Alter [J]', normalized: 'age' },
        { raw: 'Unknown', normalized: '' },
      ]

      const map = featureDefinitionsStore.definitionsByNormalized.value
      expect(Object.keys(map)).toEqual(['age'])
    })
  })
})
