<template>
  <v-container class="py-8">
    <v-sheet
        :elevation="12"
        border
        class="new-patient-card"
        rounded="lg"
    >

      <v-btn
          :to="backTarget"
          class="mb-4"
          color="primary"
          prepend-icon="mdi-arrow-left"
          size="small"
          variant="tonal"
      >
        {{ $t('form.back') }}
      </v-btn>
      <v-spacer/>
      <h1>{{ isEdit ? $t('form.title_edit') : copyEarParam === 'L' ? $t('form.title_copy_left') : copyEarParam === 'R' ? $t('form.title_copy_right') : $t('form.title') }}</h1>
      <v-spacer/>
      <form v-if="definitionsReady" class="new-patient-form" autocomplete="off" @submit.prevent="submit">
        <!-- Required-fields info banner -->
        <v-alert
          type="info"
          variant="tonal"
          density="compact"
          class="mb-4"
          icon="mdi-information-outline"
        >
          <strong>{{ $t('form.minimum_fields_title') }}:</strong>
          {{ $t('form.minimum_fields_hint') }}
        </v-alert>

        <template v-for="section in sectionedDefinitions" :key="section.name">
          <h3 class="section-title">{{ section.label }}</h3>
          <v-row dense>
            <template v-for="field in section.fields" :key="field.normalized">
              <v-col cols="12" md="6">
                <v-text-field
                  v-if="field.isDateMasked"
                  :model-value="formValues[field.normalized]"
                  @update:model-value="(val: any) => updateDateField(field.normalized, val)"
                  :label="field.label"
                  placeholder="TT.MM.JJJJ"
                  :error-messages="[]"
                  :error="(submitAttempted && field.isRequired && !field.isCheckbox && isFieldEmpty(field.normalized, field)) || !!(fieldErrorMap[field.normalized]?.length)"
                  :class="{ 'required-empty': submitAttempted && field.isRequired && !field.isCheckbox && isFieldEmpty(field.normalized, field) }"
                  color="primary"
                  hide-details
                  variant="outlined"
                  maxlength="10"
                  autocomplete="off"
                />
                <component
                  v-else
                  :is="field.component"
                  :model-value="formValues[field.normalized]"
                  @update:model-value="(val: any) => updateField(field.normalized, val)"
                  :items="field.items"
                  item-title="title"
                  item-value="value"
                  :label="field.label"
                  :error-messages="[]"
                  :error="(submitAttempted && field.isRequired && isFieldEmpty(field.normalized, field)) || !!(fieldErrorMap[field.normalized]?.length)"
                  :class="{ 'required-empty': submitAttempted && field.isRequired && !field.isCheckbox && isFieldEmpty(field.normalized, field) }"
                  :type="field.inputType"
                  :multiple="field.multiple"
                  :chips="field.multiple"
                  :closable-chips="field.multiple"
                  :clearable="field.clearable"
                  :true-value="field.trueValue"
                  :false-value="field.falseValue"
                  color="primary"
                  hide-details
                  variant="outlined"
                  autocomplete="off"
                />
              </v-col>
              <v-col
                v-if="field.otherField && isOtherSelected(field.normalized, formValues[field.normalized])"
                cols="12"
                md="6"
              >
                <v-text-field
                  :model-value="formValues[field.otherField]"
                  @update:model-value="(val: any) => updateField(field.otherField, val)"
                  :label="field.otherLabel"
                  :error-messages="[]"
                  :error="!!(fieldErrorMap[field.otherField]?.length)"
                  color="primary"
                  hide-details
                  variant="outlined"
                />
              </v-col>
            </template>
          </v-row>
          <v-divider class="my-4"/>
        </template>

        <!-- Button row -->
        <div class="new-patient-actions">
          <v-btn
              class="me-4"
              color="primary"
              type="submit"
              variant="flat"
          >
            {{ $t('form.submit') }}
          </v-btn>
          <v-btn
              class="me-4"
              color="secondary"
              type="button"
              variant="tonal"
              @click="onReset"
          >
            {{ $t('form.reset') }}
          </v-btn>
        </div>
      </form>
      <div v-else class="new-patient-form">
        <p>{{ error ?? $t('form.error.submit_failed') }}</p>
      </div>
    </v-sheet>

    <v-snackbar
        v-model="updateSuccessOpen"
        color="success"
        location="top"
        timeout="2500"
    >
      {{ $t('patient_details.update_success') }}
    </v-snackbar>

    <v-snackbar
        v-model="submitErrorOpen"
        color="error"
        location="top"
        :timeout="6000"
        multi-line
    >
      {{ submitErrorMessage }}
      <template #actions>
        <v-btn variant="text" @click="submitErrorOpen = false">OK</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>


<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {VCheckbox, VCombobox, VSelect, VTextField} from 'vuetify/components'
import {useForm} from 'vee-validate'
import i18next from 'i18next'
import {API_BASE} from '@/lib/api'
import {useRoute, useRouter} from 'vue-router'
import {useFeatureDefinitions} from '@/lib/featureDefinitions'
import {featureDefinitionsStore} from '@/lib/featureDefinitionsStore'

const language = ref(i18next.language)
i18next.on('languageChanged', (lng) => {
  language.value = lng
})

const route = useRoute()
const router = useRouter()
const rawId = route.params.id
const patientId = ref<string>(Array.isArray(rawId) ? rawId[0] : rawId ?? '')
const isEdit = computed(() => Boolean(patientId.value))
const copyFromId = computed<string | null>(() => {
  const q = route.query.copyFrom
  return typeof q === 'string' && q ? q : null
})
const copyEarParam = computed<string | null>(() => {
  const q = route.query.ear
  return typeof q === 'string' && (q === 'L' || q === 'R') ? q : null
})
const backTarget = computed(() =>
  isEdit.value ? {name: 'PatientDetail', params: {id: patientId.value}} : {name: 'SearchPatients'}
)

const submitAttempted = ref(false)
const updateSuccessOpen = ref(false)
const submitErrorOpen = ref(false)
const submitErrorMessage = ref('')

const showError = (msg: string) => {
  submitErrorMessage.value = msg
  submitErrorOpen.value = true
}
const {definitions, definitionsByNormalized, labels, sections, error} = useFeatureDefinitions()
const definitionsReady = computed(() => (definitions.value ?? []).length > 0)

const featureDefinitions = computed(() => definitionsByNormalized.value)

const resolveOptionLabel = (option: any) => {
  const lang = language.value?.startsWith('de') ? 'de' : 'en'
  return option?.labels?.[lang] ?? option?.label ?? option?.value
}

const labelFor = (name: string, fallback?: string) => {
  return labels.value?.[name] ?? fallback ?? name
}

const sectionLabelFor = (name: string, fallback?: string) => {
  return sections.value?.[name] ?? fallback ?? name
}

const getOtherValues = (name: string) =>
  computed(() => {
    const options = featureDefinitions.value?.[name]?.options
    if (!Array.isArray(options)) return []
    return options.filter((opt: any) => opt?.is_other).map((opt: any) => opt.value)
  })

const isOtherSelected = (name: string, value: unknown) => {
  return getOtherValues(name).value.includes(String(value))
}

const getOptionValueByRole = (name: string, role: string, fallback: string) => {
  const options = featureDefinitions.value?.[name]?.options
  if (!Array.isArray(options)) return fallback
  const match = options.find((opt: any) => opt?.role === role)
  return match?.value ?? fallback
}

// Computed error map – Vue tracks this as a proper reactive dependency on manualErrors
// and formErrors. Unlike a plain function call in the template, a computed guarantees
// the template re-evaluates whenever manualErrors.value is written (e.g. on submit).
const fieldErrorMap = computed<Record<string, string[]>>(() => {
  const map: Record<string, string[]> = {}
  for (const [name, msg] of Object.entries(manualErrors.value)) {
    if (msg) map[name] = [msg]
  }
  for (const [name, msg] of Object.entries(formErrors.value)) {
    if (!map[name] && msg) map[name] = [msg as string]
  }
  return map
})

const buildItems = (def: any) => {
  if (!Array.isArray(def?.options)) return undefined
  return def.options.map((opt: any) => ({
    title: resolveOptionLabel(opt),
    value: opt.value,
  }))
}

const isCheckboxField = (def: any) => {
  if (def?.type === 'boolean') return true
  if (!Array.isArray(def?.options) || def?.multiple) return false
  const roles = def.options.map((opt: any) => opt?.role).filter(Boolean)
  if (roles.includes('true') && roles.includes('false')) return true
  if (def.options.length === 2) {
    const values = def.options.map((opt: any) => String(opt?.value ?? '').toLowerCase())
    const hasPresent = values.includes('vorhanden')
    const hasNone = values.includes('kein') || values.includes('keine')
    return hasPresent && hasNone
  }
  return false
}

const getCheckboxValues = (def: any) => {
  if (!Array.isArray(def?.options)) {
    return {trueValue: 'Vorhanden', falseValue: 'Keine'}
  }
  const values = def.options.map((opt: any) => opt?.value)
  const trueValue =
    values.find((val: any) => String(val).toLowerCase() === 'vorhanden') ??
    values[0] ??
    'Vorhanden'
  const falseValue =
    values.find((val: any) => {
      const lower = String(val).toLowerCase()
      return lower === 'kein' || lower === 'keine'
    }) ??
    values[1] ??
    'Keine'
  return {trueValue, falseValue}
}

const getFieldComponent = (def: any) => {
  if (isCheckboxField(def)) return VCheckbox
  // Fixed-options multi-select → VSelect (supports chips + closable-chips)
  if (def?.multiple && Array.isArray(def?.options)) return VSelect
  // Free-text multi-select (no fixed options) → VCombobox
  if (def?.multiple) return VCombobox
  if (Array.isArray(def?.options)) return VSelect
  return VTextField
}

const sectionedDefinitions = computed(() => {
  const defs = definitions.value ?? []
  const otherFieldNames = new Set(
    defs.map((def: any) => def?.other_field).filter(Boolean)
  )
  const order: string[] = []
  const grouped: Record<string, any[]> = {}

  for (const def of defs) {
    if (!def?.normalized) continue
    if (otherFieldNames.has(def.normalized)) continue
    const section = def.section ?? 'Weitere'
    if (!order.includes(section)) order.push(section)
    grouped[section] = grouped[section] ?? []
    grouped[section].push(def)
  }

  const filtered = order.filter((section) => section !== 'Weitere')
  const visibleSections = filtered.length > 0 ? filtered : order

  return visibleSections.map((section) => ({
      name: section,
      label: sectionLabelFor(section),
      fields: (grouped[section] ?? []).map((def: any) => {
        const isRequired = def.required === true
        const baseLabel = labelFor(def.normalized, def.description ?? def.raw)
        return {
        normalized: def.normalized,
        label: isRequired ? `${baseLabel} *` : baseLabel,
        isRequired,
        isCheckbox: isCheckboxField(def),
        component: getFieldComponent(def),
        inputType: def.input_type === 'number' ? 'number' : undefined,
        isDateMasked: def.input_type === 'date',
        items: buildItems(def),
        multiple: Boolean(def.multiple),
        // Allow clearing for any dropdown (VSelect/VCombobox) but not checkboxes
        clearable: !isCheckboxField(def) && Array.isArray(def?.options),
        trueValue: isCheckboxField(def)
          ? getCheckboxValues(def).trueValue
          : getOptionValueByRole(def.normalized, 'true', 'Vorhanden'),
        falseValue: isCheckboxField(def)
          ? getCheckboxValues(def).falseValue
          : getOptionValueByRole(def.normalized, 'false', 'Keine'),
        otherField: def.other_field,
        otherLabel: def.other_field ? labelFor(def.other_field, def.other_field) : undefined,
      }})
    }))
})

  // Helper used by the template to determine if a field is empty
  const isFieldEmpty = (name: string, field: any) => {
    const val = (formValues as any)[name]
    if (field?.multiple) return !Array.isArray(val) || val.length === 0
    if (field?.inputType === 'number') {
      if (val === undefined || val === null || val === '') return true
      const numeric = typeof val === 'number' ? val : Number(val)
      return !Number.isFinite(numeric)
    }
    return val === undefined || val === null || val === ''
  }

const validationSchema = computed(() => {
  // Read language.value to register it as a reactive dependency so the schema
  // re-evaluates when the UI language switches (e.g. DE ↔ EN).
  void language.value
  const defs = definitions.value ?? []
  const schema: Record<string, any> = {}

  const requiredMessageFor = (def: any) => {
    const key = `form.error.${def?.normalized}`
    const msg = i18next.t(key)
    return msg !== key ? msg : i18next.t('form.error.required_field')
  }

  const isEmptyValue = (value: unknown, def: any) => {
    if (def?.multiple) return !Array.isArray(value) || value.length === 0
    if (def?.input_type === 'number') {
      if (value === undefined || value === null || value === '') return true
      const numericValue = typeof value === 'number' ? value : Number(value)
      return !Number.isFinite(numericValue)
    }
    return value === undefined || value === null || value === ''
  }

  const getAllowedValues = (def: any) => {
    if (def?.validation?.type === 'enum_one_of') {
      return Array.isArray(def.validation.allowed) ? def.validation.allowed : []
    }
    if (Array.isArray(def?.options)) {
      return def.options.map((opt: any) => opt.value)
    }
    return []
  }

  for (const def of defs) {
    if (!def?.normalized) continue
    const allowed = getAllowedValues(def)

    schema[def.normalized] = (value: unknown) => {
      // Enum/select fields always receive a fallback via withDefault on submit; skip required-empty check
      if (def.required && isEmptyValue(value, def)) return requiredMessageFor(def)
      if (!isEmptyValue(value, def) && allowed.length > 0) {
        if (def.multiple && Array.isArray(value)) {
          const normalized = normalizeImagingValue(value)
          const allAllowed = normalized.every((entry) => allowed.includes(entry))
          if (!allAllowed) return requiredMessageFor(def)
        } else if (!allowed.includes(value as any)) {
          return requiredMessageFor(def)
        }
      }
      return true
    }

    if (def.other_field) {
      schema[def.other_field] = (value: unknown, ctx: any) => {
        if (isOtherSelected(def.normalized, ctx?.form?.[def.normalized])) {
          if (value === undefined || value === null || value === '') return requiredMessageFor(def)
        }
        return true
      }
    }
  }

  return schema
})

const {handleSubmit, handleReset, setFieldTouched, setFieldValue, values, errors} = useForm({
  validationSchema,
})

const formValues = values
const formErrors = computed(() => errors.value ?? {})

// Single source of truth for field-level error messages shown in the UI.
// Populated synchronously on submit, cleared per-field when the user edits.
const manualErrors = ref<Record<string, string>>({})

const clearManualError = (name: string) => {
  if (manualErrors.value[name]) {
    const copy = { ...manualErrors.value }
    delete copy[name]
    manualErrors.value = copy
  }
}

// The three minimum fields that the backend requires for a prediction
const MINIMUM_PREDICTION_FIELDS = ['gender', 'age', 'hl_operated_ear']

const highlightEmptyMinimumFields = () => {
  const fallback = i18next.t('form.error.required_field')
  const errs = { ...manualErrors.value }
  for (const name of MINIMUM_PREDICTION_FIELDS) {
    const val = (values as any)[name]
    const empty = val === undefined || val === null || val === ''
    if (empty) {
      const key = `form.error.${name}`
      const msg = i18next.t(key)
      errs[name] = msg !== key ? msg : fallback
    }
  }
  manualErrors.value = errs
}

const highlightEmptyRequiredFields = () => {
  const defs = definitions.value ?? []
  const fallback = i18next.t('form.error.required_field')
  const errs = { ...manualErrors.value }
  for (const def of defs) {
    if (!def?.required || !def?.normalized) continue
    if (isCheckboxField(def)) continue
    const val = (values as any)[def.normalized]
    const empty = def.multiple
      ? !Array.isArray(val) || val.length === 0
      : val === undefined || val === null || val === ''
    if (empty) {
      const key = `form.error.${def.normalized}`
      const msg = i18next.t(key)
      errs[def.normalized] = msg !== key ? msg : fallback
    }
  }
  manualErrors.value = errs
}

const updateField = (name: string, value: any) => {
  setFieldValue(name, value)
  clearManualError(name)
}

const formatDateInput = (raw: string): string => {
  const digits = raw.replace(/\D/g, '').slice(0, 8)
  if (digits.length <= 2) return digits
  if (digits.length <= 4) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  return `${digits.slice(0, 2)}.${digits.slice(2, 4)}.${digits.slice(4)}`
}

const calculateAgeFromDate = (dateStr: string): number | null => {
  // Expects DD.MM.YYYY format
  const parts = dateStr.split('.')
  if (parts.length !== 3 || parts[2].length !== 4) return null
  const day = parseInt(parts[0], 10)
  const month = parseInt(parts[1], 10) - 1
  const year = parseInt(parts[2], 10)
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null
  const birth = new Date(year, month, day)
  if (isNaN(birth.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age >= 0 && age <= 150 ? age : null
}

const updateDateField = (name: string, val: any) => {
  const str = typeof val === 'string' ? val : ''
  const formatted = formatDateInput(str)
  setFieldValue(name, formatted)
  clearManualError(name)
  // Auto-fill age when birth_date is completely entered
  if (name === 'birth_date' && formatted.length === 10) {
    const age = calculateAgeFromDate(formatted)
    if (age !== null) {
      setFieldValue('age', age)
      clearManualError('age')
    }
  }
}

const normalizeImagingValue = (val: unknown): string[] => {
  if (Array.isArray(val)) {
    return val
      .map((entry: any) => (entry && typeof entry === 'object' ? entry.value : entry))
      .filter((entry) => entry !== undefined && entry !== null && entry !== '')
      .map((entry) => String(entry))
  }
  if (val === undefined || val === null || val === '') return []
  if (typeof val === 'object') {
    const value = (val as any)?.value
    return value === undefined || value === null || value === '' ? [] : [String(value)]
  }
  return [String(val)]
}

const formFieldNames = computed(() => Object.keys(definitionsByNormalized.value ?? {}))


const withDefault = (value: any, fallback = 'Keine') => {
  if (Array.isArray(value)) return value.length ? value : fallback
  if (value === undefined || value === null || value === '') return fallback
  return value
}


const normalizeErrors = (errors: object | null | undefined) => {
  const toMessage = (err: unknown): string | undefined => {
    if (!err) return undefined
    if (typeof err === 'string') return err
    if (err instanceof Error) return err.message
    if (Array.isArray(err)) {
      const nested = err.map(toMessage).filter(Boolean) as string[]
      return nested.length ? nested.join('\n') : undefined
    }
    if (typeof err === 'object') {
      try {
        const serialized = JSON.stringify(err)
        return serialized === '{}' ? undefined : serialized
      } catch (e) {
        return String(err)
      }
    }
    return String(err)
  }

  const messages: string[] = []
  Object.values(errors || {}).forEach(err => {
    const msg = toMessage(err)
    if (msg) messages.push(msg)
  })
  return messages
}

const stableStringify = (value: any): string => {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`
  const keys = Object.keys(value).sort()
  const entries = keys.map(k => `${JSON.stringify(k)}:${stableStringify(value[k])}`)
  return `{${entries.join(',')}}`
}

const buildSnapshot = (formValues: Record<string, any>) => {
  const displayName = [formValues.last_name, formValues.first_name].filter(Boolean).join(", ")
  return {
    display_name: displayName || null,
    input_features: buildInputFeatures(formValues),
  }
}

const splitImagingTypes = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.map(v => String(v).trim()).filter(Boolean)
  if (typeof value !== 'string') return []
  return value
    .split(',')
    .map(v => v.trim())
    .filter(Boolean)
    .map(v => {
      const lower = v.toLowerCase()
      if (lower === 'ct') return 'CT'
      if (lower === 'mrt') return 'MRT'
      if (lower === 'konventionell') return 'Konventionell'
      return v
    })
}

const buildInputFeatures = (values: Record<string, any>) => {
  const input_features: Record<string, any> = {}
  const defs = Object.values(definitionsByNormalized.value ?? {})

  for (const def of defs) {
    if (!def?.raw || def.ui_only) continue
    let value = values[def.normalized]

    if (def.other_field && isOtherSelected(def.normalized, value)) {
      value = values[def.other_field]
    }

    if (def.multiple) {
      const normalized = normalizeImagingValue(value)
      value = normalized.join(', ')
    } else if (def.input_type === 'number') {
      value = Number(value)
    } else if (typeof value === 'boolean') {
      value = getOptionValueByRole(def.normalized, value ? 'true' : 'false', value ? 'Vorhanden' : 'Keine')
    } else if (Array.isArray(def.options)) {
      // For enum fields, only use a fallback that is actually a valid option value
      const optionValues = def.options.map((opt: any) => opt.value)
      if (value === undefined || value === null || value === '') {
        const roleFallback = getOptionValueByRole(def.normalized, 'false', '')
        value = optionValues.includes(roleFallback) ? roleFallback : ''
      }
    } else {
      value = value ?? ''
    }

    input_features[def.raw] = value
  }

  return input_features
}

const initialSnapshot = ref<string | null>(null)

const populateFormForEdit = (patient: any) => {
  const input = patient?.input_features || {}
  const displayName = String(patient?.display_name || '')
  let first = ''
  let last = ''
  if (displayName.includes(',')) {
    const parts = displayName.split(',').map(p => p.trim())
    last = parts[0] || ''
    first = parts.slice(1).join(', ').trim()
  } else if (displayName.includes(' ')) {
    const parts = displayName.split(' ').filter(Boolean)
    first = parts[0] || ''
    last = parts.slice(1).join(' ').trim()
  } else {
    last = displayName
  }

  setFieldValue('first_name', first)
  setFieldValue('last_name', last)

  const defs = definitions.value ?? []
  for (const def of defs) {
    if (!def?.normalized || def.ui_only) continue
    if (def.normalized === 'first_name' || def.normalized === 'last_name') continue
    const rawValue = input?.[def.raw]

    if (def.multiple) {
      const split = splitImagingTypes(rawValue)
      const optionValues = (def.options ?? []).map((opt: any) => opt.value)
      const filtered = optionValues.length > 0 ? split.filter((v: string) => optionValues.includes(v)) : split
      setFieldValue(def.normalized, filtered)
      continue
    }

    if (Array.isArray(def.options)) {
      const optionValues = def.options.map((opt: any) => opt.value)
      if (optionValues.includes(rawValue)) {
        setFieldValue(def.normalized, rawValue)
      } else if (def.other_field && rawValue !== undefined && rawValue !== null && rawValue !== '' && rawValue !== 'Keine') {
        const otherOptions = getOtherValues(def.normalized).value
        if (otherOptions.length) {
          setFieldValue(def.normalized, otherOptions[0])
          setFieldValue(def.other_field, rawValue)
        } else {
          setFieldValue(def.normalized, rawValue)
        }
      } else {
        // Clear invalid values like 'Keine' that aren't actual option values
        setFieldValue(def.normalized, '')
      }
      continue
    }

    // For non-enum text fields, treat stored 'Keine' as empty in edit mode
    const cleanValue = rawValue === 'Keine' ? '' : (rawValue ?? '')
    setFieldValue(def.normalized, cleanValue)
  }

  initialSnapshot.value = stableStringify(buildSnapshot(values as Record<string, any>))
}

const onSubmit = handleSubmit(
  async values => {
    try {
      const payload = buildSnapshot(values)
      if (isEdit.value && initialSnapshot.value === stableStringify(payload)) {
        submitAttempted.value = false
        await router.push({name: 'PatientDetail', params: {id: patientId.value}})
        return
      }

      const method = isEdit.value ? 'PUT' : 'POST'
      const url = isEdit.value
        ? `${API_BASE}/api/v1/patients/${encodeURIComponent(patientId.value)}`
        : `${API_BASE}/api/v1/patients/`

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          accept: 'application/json',
        },
        body: JSON.stringify({
          input_features: payload.input_features,
          display_name: payload.display_name || undefined,
        }),
      })

      if (!response.ok) {
        const contentType = response.headers.get('content-type') || ''
        let errorMessage = 'Failed to create patient'
        try {
          if (contentType.includes('application/json')) {
            const data = await response.json()
            const rawDetail = (data?.detail as string) ?? JSON.stringify(data)
            // Translate minimum-fields backend error to current UI language
            if (rawDetail && rawDetail.includes('Mindestfelder')) {
              errorMessage = i18next.t('form.minimum_fields_error')
              // Highlight the minimum prediction fields that are empty
              highlightEmptyMinimumFields()
            } else if (rawDetail && rawDetail.includes('Pflichtfelder')) {
              errorMessage = i18next.t('form.required_fields_error')
              // Highlight all empty required fields
              highlightEmptyRequiredFields()
            } else {
              errorMessage = rawDetail
            }
          } else {
            const text = await response.text()
            errorMessage = text || errorMessage
          }
        } catch (e) {
          // fall back to default message
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      if (isEdit.value) {
        submitAttempted.value = false
        await router.push({name: 'PatientDetail', params: {id: patientId.value}, query: {updated: '1'}})
      } else {
        submitAttempted.value = false
        await router.push({name: 'PatientDetail', params: {id: data.id}, query: {created: '1'}})
      }
    } catch (err: any) {
      showError(err?.message ?? i18next.t('form.error.submit_failed'))
    }
  },
  (ctx) => {
    formFieldNames.value.forEach(name => setFieldTouched(name, true))
    const messages = normalizeErrors(ctx as object)
    showError(messages.length ? messages.join('\n') : i18next.t('form.error.fix_fields'))
  }
)

const submit = async () => {
  // Synchronously compute which required fields are empty and store in manualErrors.
  // This avoids all async timing issues with vee-validate error propagation.
  const defs = definitions.value ?? []
  const newErrors: Record<string, string> = {}
  const fallbackMsg = i18next.t('form.error.required_field')
  for (const def of defs) {
    if (!def?.required || !def?.normalized) continue
    // VCheckbox fields always carry trueValue/falseValue – never empty.
    // We still skip them here because they can never be "empty" in the required sense.
    // All other fields (VTextField, VSelect, VCombobox, date) are validated.
    const val = (values as any)[def.normalized]
    const isEmpty = def.multiple
      ? !Array.isArray(val) || val.length === 0
      : def.input_type === 'number'
        ? val === undefined || val === null || val === '' || !Number.isFinite(Number(val))
        : val === undefined || val === null || val === ''
    if (isEmpty && !isCheckboxField(def)) {
      const fieldKey = `form.error.${def.normalized}`
      const fieldMsg = i18next.t(fieldKey)
      newErrors[def.normalized] = fieldMsg !== fieldKey ? fieldMsg : fallbackMsg
    }
  }
  manualErrors.value = newErrors
  submitAttempted.value = true

  if (Object.keys(newErrors).length > 0) {
    showError(i18next.t('form.error.fix_fields'))
    return
  }

  await onSubmit()
}

const onReset = () => {
  submitAttempted.value = false
  manualErrors.value = {}
  handleReset()
}

onMounted(async () => {
  if (!definitionsReady.value) {
    await featureDefinitionsStore.loadDefinitions()
    await featureDefinitionsStore.loadLabels(language.value)
  }
  if (isEdit.value) {
    // Edit mode: load existing patient data
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(patientId.value)}`,
        {
          method: 'GET',
          headers: {accept: 'application/json'},
        }
      )
      if (!response.ok) throw new Error('Failed to load patient')
      const data = await response.json()
      populateFormForEdit(data)
    } catch (err) {
      console.error(err)
      showError(err instanceof Error ? err.message : 'Failed to load patient')
    }
  } else if (copyFromId.value) {
    // Copy mode: pre-fill from another patient and flip the ear side
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(copyFromId.value)}`,
        {
          method: 'GET',
          headers: {accept: 'application/json'},
        }
      )
      if (!response.ok) throw new Error('Failed to load source patient')
      const data = await response.json()
      populateFormForEdit(data)
      // Flip ear side: R → L, L → R
      const currentSide = data?.input_features?.['Seiten']
      const otherSide = currentSide === 'R' ? 'L' : currentSide === 'L' ? 'R' : null
      if (otherSide) setFieldValue('operated_side', otherSide)
      // Reset snapshot so this is treated as a brand-new patient (never as an edit)
      initialSnapshot.value = null
    } catch (err) {
      console.error('Failed to copy patient data:', err)
    }
  }
})
</script>


<style scoped>
.new-patient-card {
  padding: 32px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}

/* space between title and first row */
.new-patient-card h1 {
  margin: 8px 0 24px 0;
}

.section-title {
  margin: 12px 0 8px;
  font-weight: 600;
}

.field-description {
  margin: 4px 0 6px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.92rem;
}

/* form layout */
.new-patient-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* buttons aligned like in the mockup */
.new-patient-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

/* Prominent red border for unfilled required fields after submit attempt */
:deep(.v-field--error .v-field__outline) {
  --v-field-border-width: 2px;
  color: rgb(var(--v-theme-error)) !important;
}

:deep(.v-field--error) {
  border-radius: 4px;
  box-shadow: 0 0 0 2px rgba(var(--v-theme-error), 0.35);
}

/* Red asterisk for required field labels */
:deep(.v-field--error .v-label) {
  color: rgb(var(--v-theme-error)) !important;
  font-weight: 600;
}

/* ── Required-empty: red outline for Vuetify 3 outlined fields ──────────────
 *
 * Root cause: Vuetify 3 outlined variant renders borders via
 *   `border-color: currentColor`
 * on .v-field__outline__start / __end / __notch::before / ::after.
 * `currentColor` inherits from the nearest ancestor that carries a `color`
 * value — which is .v-field itself.
 *
 * Fix: set `color` (not `border-color`) on .v-field, then also explicitly set
 * border-color on every segment as belt-and-suspenders.
 * ───────────────────────────────────────────────────────────────────────── */

/* Step 1 – The field container carries the "accent" color that currentColor
   resolves to inside every child outline segment. */
.required-empty :deep(.v-field) {
  color: rgb(var(--v-theme-error)) !important;
  --v-field-border-opacity: 1 !important;
  box-shadow: 0 0 0 1px rgba(var(--v-theme-error), 0.28) !important;
}

/* Step 2 – Outline wrapper: propagate color downward explicitly */
.required-empty :deep(.v-field__outline) {
  color: rgb(var(--v-theme-error)) !important;
  opacity: 1 !important;
}

/* Step 3 – Left and right border bars */
.required-empty :deep(.v-field__outline__start),
.required-empty :deep(.v-field__outline__end) {
  border-color: rgb(var(--v-theme-error)) !important;
  border-width: 2px !important;
  opacity: 1 !important;
}

/* Step 4 – Notch (label gap): color on the element so ::before/::after inherit */
.required-empty :deep(.v-field__outline__notch) {
  color: rgb(var(--v-theme-error)) !important;
  border-color: rgb(var(--v-theme-error)) !important;
}

/* Step 5 – Notch pseudo-elements draw the top-border lines beside the label */
.required-empty :deep(.v-field__outline__notch::before),
.required-empty :deep(.v-field__outline__notch::after) {
  border-top-color: rgb(var(--v-theme-error)) !important;
  border-width: 2px !important;
}

/* Step 6 – Red label text */
.required-empty :deep(.v-label) {
  color: rgb(var(--v-theme-error)) !important;
  opacity: 1 !important;
}
</style>
