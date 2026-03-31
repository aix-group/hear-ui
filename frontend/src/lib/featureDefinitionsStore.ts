import {ref, computed, readonly, type Ref} from 'vue'
import i18next from 'i18next'
import {API_BASE} from '@/lib/api'
import {logger} from '@/lib/logger'

export type FeatureOption = {
  value: string
  labels?: Record<string, string>
  role?: string
  is_other?: boolean
}

export type FeatureDefinition = {
  raw: string
  normalized: string
  description?: string
  section?: string
  type?: string
  required?: boolean
  options?: FeatureOption[]
  input_type?: string
  multiple?: boolean
  other_field?: string
  ui_only?: boolean
}

type FeatureDefinitionsState = {
  definitions: Ref<FeatureDefinition[]>
  definitionsByNormalized: Ref<Record<string, FeatureDefinition>>
  labels: Ref<Record<string, string>>
  sections: Ref<Record<string, string>>
  sectionOrder: Ref<string[]>
  error: Ref<string | null>
  loading: Ref<boolean>
  loadDefinitions: () => Promise<void>
  loadLabels: (locale?: string) => Promise<void>
}

const definitions = ref<FeatureDefinition[]>([])
const labels = ref<Record<string, string>>({})
const sections = ref<Record<string, string>>({})
const sectionOrder = ref<string[]>([])
const error = ref<string | null>(null)
const loading = ref(false)

const definitionsByNormalized = computed(() => {
  return Object.fromEntries(
    definitions.value
      .filter((entry) => entry?.normalized)
      .map((entry) => [entry.normalized, entry])
  )
})

const loadDefinitions = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/api/v1/features/definitions`, {
      method: 'GET',
      headers: {accept: 'application/json'},
    })
    const contentType = response.headers.get('content-type') || ''
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `Failed to load feature definitions (${response.status})`)
    }
    if (!contentType.includes('application/json')) {
      const text = await response.text()
      throw new Error(text || 'Feature definitions response is not JSON')
    }
    const data = await response.json()
    definitions.value = Array.isArray(data?.features) ? data.features : []
    sectionOrder.value = Array.isArray(data?.section_order) ? data.section_order : []
    error.value = null
  } catch (err) {
    logger.error(err)
    definitions.value = []
    sectionOrder.value = []
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

const loadLabels = async (locale?: string) => {
  const lang = locale ?? i18next.language
  try {
    const response = await fetch(`${API_BASE}/api/v1/features/locales/${encodeURIComponent(lang)}`, {
      method: 'GET',
      headers: {accept: 'application/json'},
    })
    const contentType = response.headers.get('content-type') || ''
    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `Failed to load feature locales (${response.status})`)
    }
    if (!contentType.includes('application/json')) {
      const text = await response.text()
      throw new Error(text || 'Feature locales response is not JSON')
    }
    const data = await response.json()
    labels.value = data?.labels ?? {}
    sections.value = data?.sections ?? {}
    error.value = null
  } catch (err) {
    logger.error(err)
    labels.value = {}
    sections.value = {}
    error.value = err instanceof Error ? err.message : String(err)
  }
}

export const featureDefinitionsStore: FeatureDefinitionsState = {
  definitions,
  definitionsByNormalized: computed(() => definitionsByNormalized.value) as Ref<Record<string, FeatureDefinition>>,
  labels,
  sections,
  sectionOrder,
  error,
  loading,
  loadDefinitions,
  loadLabels,
}

export const useFeatureDefinitionsStore = () => readonly(featureDefinitionsStore)
