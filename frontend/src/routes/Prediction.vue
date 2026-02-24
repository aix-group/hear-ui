<template>
  <v-container class="py-8">
    <v-sheet
      :elevation="12"
      border
      class="prediction-sheet"
      rounded="lg"
    >
      <!-- Title -->
      <v-row justify="start" no-gutters>
        <h1>
          {{ $t('prediction.title') }}
          <span class="text-primary">{{ patient_name }}</span><span v-if="patient_birth_date" class="text-primary">, {{ patient_birth_date }}</span>
        </h1>

      </v-row>
      <v-divider
        class="my-6"
      />

      <!-- Out-of-scope / data-quality warnings -->
      <v-row v-if="predictionWarnings.length > 0" class="mb-4" no-gutters>
        <v-col cols="12">
          <v-alert
            v-for="(warn, i) in predictionWarnings"
            :key="i"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-2"
            icon="mdi-alert-circle-outline"
            border="start"
          >
            {{ warn }}
          </v-alert>
        </v-col>
      </v-row>

      <!-- Results -->
      <v-row
        justify="start"
        align="center"
        no-gutters
      >
        <!-- Result -->
        <v-col cols="7">
          <h2>{{ $t('prediction.result.title') }}</h2>
          <h1 class="prediction-value">{{ (predictionResult * 100).toFixed(0) }}%</h1>
          <p>{{ $t('prediction.result.probability') }}</p>

          <v-divider
            class="my-2"
          />

          <div
            class="prediction-status"
            :class="recommended ? 'status-success' : 'status-error'"
          >
            {{
              recommended
                ? $t('prediction.result.status.recommended')
                : $t('prediction.result.status.not_recommended')
            }}
          </div>


          <p>
            {{
              recommended
                ? $t('prediction.result.description.recommended')
                : $t('prediction.result.description.not_recommended')
            }}
          </p>

        </v-col>

        <!-- Graph -->
        <v-col class="graph-col" cols="5">
          <v-sheet class="graph-sheet" rounded="lg">
            <!-- Title -->
            <h4 class="graph-title">
              {{ $t('prediction.result.graph.title') }}
            </h4>

            <v-sheet class="graph-canvas" rounded="lg" elevation="0">
              <!-- GRAPH AREA -->
              <div class="graph-placeholder graph-placeholder-relative"
                   :style="{'--patient-x-position': patientX + '%'}">
                <svg
                  class="graph-svg"
                  viewBox="0 33.33 100 66.67"
                >
                  <!-- curved “probability” line -->
                  <path
                    class="graph-curve"
                    :d="graphPath"
                  />

                  <!-- vertical dotted line at patient % -->
                  <line
                    class="graph-patient-line"
                    :x1="patientX"
                    y1="0"
                    :x2="patientX"
                    y2="100"
                  />

                  <!-- blue patient dot -->
                  <circle
                    class="graph-patient-dot"
                    :cx="patientX"
                    :cy="patientY"
                    r="1.5"
                  />
                </svg>

                <!-- label: 'Patient: XX%' -->
                <div class="graph-patient-label" :class="recommended ? 'label-left' : 'label-right'">
                  {{ $t('prediction.result.graph.patient') }} {{ patientPercent }}%
                </div>
              </div>


              <!-- X-axis -->
              <div class="graph-x-axis"></div>
              <div class="graph-scale">
                <span>0</span>
                <span>100</span>
              </div>
            </v-sheet>


            <!-- Caption -->
            <p class="graph-caption">
              {{ $t('prediction.result.graph.description', { threshold: thresholdPercent ?? 0 }) }}
            </p>
          </v-sheet>
        </v-col>


      </v-row>
      <v-divider
        class="my-6"
      />

      <!-- Explanations -->
      <v-row
        justify="start"
        align="center"
        no-gutters
      >
        <v-col cols="12">
          <h2 class="mb-2">
            {{ $t('prediction.explanations.title') }}
          </h2>
          <p class="text-body-2 text-medium-emphasis mb-4">
            {{ $t('prediction.explanations.subtitle') }}
          </p>

          <!-- Plotly SHAP-style bar chart -->
          <div
            ref="explanationPlot"
            :style="{ width: '100%', height: explanationPlotHeight + 'px' }"
          ></div>
        </v-col>
      </v-row>

      <!-- What-If Analysis Panel -->
      <v-row class="mt-2" no-gutters>
        <v-col cols="12">
          <v-btn
            :prepend-icon="whatIfOpen ? 'mdi-chevron-up' : 'mdi-flask-outline'"
            color="primary"
            variant="tonal"
            size="small"
            class="mb-3"
            @click="whatIfOpen = !whatIfOpen"
          >
            {{ $t('prediction.whatif.toggle') }}
          </v-btn>

          <v-expand-transition>
            <v-card v-if="whatIfOpen" variant="outlined" color="primary" class="pa-4">
              <div class="text-body-2 text-medium-emphasis mb-4">{{ $t('prediction.whatif.description') }}</div>

              <!-- Feature overrides: wrap in form with autocomplete=off to suppress browser suggestion bubbles -->
              <form autocomplete="off" @submit.prevent="">
              <v-row dense>
                <v-col
                  v-for="feat in whatIfFeatures"
                  :key="feat.rawKey"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <!-- Numeric slider -->
                  <template v-if="feat.inputType === 'number'">
                    <div class="text-caption mb-1">{{ feat.label }}</div>
                    <div style="display:flex; align-items:center; gap:8px">
                      <v-slider
                        v-model="whatIfValues[feat.rawKey]"
                        :min="feat.sliderMin"
                        :max="feat.sliderMax"
                        :step="feat.sliderStep"
                        thumb-label
                        color="primary"
                        density="compact"
                        hide-details
                        style="flex:1"
                        @update:model-value="onWhatIfChange"
                      />
                      <v-btn v-if="feat.normalized !== 'age'" icon size="x-small" class="whatif-remove-btn" title="Remove override" @click="clearWhatIf(feat.rawKey)">
                        <v-icon class="whatif-remove-icon" size="16">mdi-close</v-icon>
                      </v-btn>
                    </div>
                  </template>
                  <!-- Categorical select -->
                  <template v-else-if="feat.options">
                    <div style="display:flex; align-items:center; gap:8px">
                      <v-select
                        v-model="whatIfValues[feat.rawKey]"
                        :label="feat.label"
                        :items="feat.options"
                        item-title="title"
                        item-value="value"
                        density="compact"
                        variant="outlined"
                        hide-details
                        class="mb-2"
                        autocomplete="off"
                        no-filter
                        style="flex:1"
                        :menu-props="{ closeOnContentClick: true }"
                        @update:model-value="onWhatIfChange"
                      />
                      <v-btn v-if="feat.normalized !== 'age'" icon size="x-small" class="whatif-remove-btn" title="Remove override" @click="clearWhatIf(feat.rawKey)">
                        <v-icon class="whatif-remove-icon" size="16">mdi-close</v-icon>
                      </v-btn>
                    </div>
                  </template>
                </v-col>
              </v-row>
              </form>

              <!-- Result comparison -->
              <v-divider class="my-4" />
              <div class="d-flex align-center ga-6 flex-wrap">
                <div class="text-center">
                  <div class="text-caption text-medium-emphasis">{{ $t('prediction.whatif.original') }}</div>
                  <div class="text-h5 font-weight-bold" :class="recommended ? 'text-success' : 'text-error'">
                    {{ (predictionResult * 100).toFixed(0) }}%
                  </div>
                </div>
                <v-icon size="32" color="grey">mdi-arrow-right</v-icon>
                <div class="text-center">
                  <div class="text-caption text-medium-emphasis">{{ $t('prediction.whatif.modified') }}</div>
                  <div v-if="whatIfLoading" class="text-h5">
                    <v-progress-circular indeterminate size="28" width="2" color="primary"/>
                  </div>
                  <div
                    v-else-if="whatIfPrediction !== null"
                    class="text-h5 font-weight-bold"
                    :class="whatIfPrediction > (threshold ?? 0.5) ? 'text-success' : 'text-error'"
                  >
                    {{ (whatIfPrediction * 100).toFixed(0) }}%
                  </div>
                  <div v-else class="text-h5 text-grey">—</div>
                </div>
                <div v-if="whatIfPrediction !== null" class="text-body-2">
                  <v-chip
                    :color="whatIfDelta > 0 ? 'success' : whatIfDelta < 0 ? 'error' : 'default'"
                    size="small"
                    variant="tonal"
                  >
                    {{ whatIfDelta > 0 ? '+' : '' }}{{ (whatIfDelta * 100).toFixed(1) }} Pp
                  </v-chip>
                </div>
              </div>
            </v-card>
          </v-expand-transition>
        </v-col>
      </v-row>


      <v-divider
        class=" my-6
          "
      />

      <!-- Actions -->
      <div class="d-flex justify-space-between align-center mb-4">
        <v-btn
          :to="{ name: 'PatientDetail', params: { id: patient_id } }"
          color="primary"
          prepend-icon="mdi-arrow-left"
          variant="tonal"
        >
          {{ $t('prediction.back') }}
        </v-btn>

        <v-btn
          color="primary"
          variant="flat"
          @click="showFeedback = true"
        >
          {{ $t('prediction.give_feedback') }}
        </v-btn>

        <v-dialog v-model="showFeedback" max-width="600">
          <v-card>
            <v-card-title>
              {{ $t('prediction.give_feedback') }}
            </v-card-title>

            <v-card-text>
              <FeedbackForm
                :predictionData="{
                  prediction: predictionResult,
                  explanation: prediction.params
                }"
                :patientData="{
                  age: 0,
                  hearing_loss_duration: 0,
                  implant_type: 'unknown'
                }"
                @feedbackSubmitted="showFeedback = false"
              />
            </v-card-text>
          </v-card>
        </v-dialog>

      </div>


    </v-sheet>
  </v-container>
</template>

<script lang="ts" setup>
import {useRoute, useRouter} from 'vue-router'
import {computed, onMounted, onBeforeUnmount, ref, watch} from 'vue'
import * as Plotly from 'plotly.js-dist-min'
import {API_BASE} from "@/lib/api";
import i18next from 'i18next'
import FeedbackForm from '@/components/FeedbackForm.vue'
import {useFeatureDefinitions} from '@/lib/featureDefinitions'
import {featureDefinitionsStore} from '@/lib/featureDefinitionsStore'
import {formatBirthDateLocale} from '@/utils'

const route = useRoute()
const router = useRouter()
const patient_name = ref("")
const rawBirthDate = ref<string | null>(null)
const rawId = route.params.patient_id
const showFeedback = ref(false)

const patient_id = ref<string>(Array.isArray(rawId) ? rawId[0] : (rawId as string) ?? "")
const prediction = ref<{
  result: number;
  params: Record<string, number>;
  feature_values?: Record<string, number>;
}>({
  result: 0,
  params: {},
  feature_values: {}
})
const patientInputFeatures = ref<Record<string, unknown>>({})
const loading = ref(true)
const error = ref<string | null>(null)
const predictionWarnings = ref<string[]>([])

// What-if analysis state
const whatIfOpen = ref(false)
const whatIfValues = ref<Record<string, any>>({})
const initialWhatIfValues = ref<Record<string, any>>({})
const whatIfPrediction = ref<number | null>(null)
const whatIfLoading = ref(false)
let whatIfDebounce: ReturnType<typeof setTimeout> | null = null
const whatIfDelta = computed(() =>
  whatIfPrediction.value !== null ? whatIfPrediction.value - predictionResult.value : 0
)

if (!patient_id.value) {
  router.replace({name: "NotFound"})
}

const language = ref(i18next.language)
const onLanguageChanged = (lng: string) => {
  language.value = lng
}
i18next.on('languageChanged', onLanguageChanged)

// Computed birth date — re-formats automatically when language changes
const patient_birth_date = computed(() => formatBirthDateLocale(rawBirthDate.value, language.value))
const {definitions, labels, sections} = useFeatureDefinitions()

const threshold = ref<number | null>(null)
const thresholdPercent = computed(() => {
  if (threshold.value === null) return null
  return Math.round(threshold.value * 100)
})
const predictionResult = computed(() => prediction.value?.result ?? 0)
const recommended = computed(() => {
  if (threshold.value === null) return false
  return predictionResult.value > threshold.value
})

const GRAPH_SCALE_FACTOR = 200 // Larger number = flatter curve
const MAX_Y_COORD = 96 // Max Y coordinate in SVG viewBox

// 0–100 %
const patientPercent = computed(() => Math.round(predictionResult.value * 100))

// x coordinate in SVG (viewBox width = 100)
const patientX = computed(() => patientPercent.value)

const patientY = computed(() => {
  const x = patientX.value
  return MAX_Y_COORD - (x * x / GRAPH_SCALE_FACTOR)
})

const graphPath = computed(() => {
  let path = `M 0 ${MAX_Y_COORD}`
  for (let x = 1; x <= 100; x += 5) {
    const y = MAX_Y_COORD - (x * x / GRAPH_SCALE_FACTOR)
    path += ` L ${x},${y}`
  }
  return path
})

/* ---------- Plotly Explanations chart ---------- */

const explanationPlot = ref<HTMLDivElement | null>(null)

const matchedFeatures = computed(() => {
  const byKey = prediction.value?.params ?? {}
  const availableKeys = Object.keys(byKey)
  const features: Array<{
    rawKey: string
    normalizedKey: string
    description?: string
    section?: string
    featureKey: string
    importance: number
    rawValue: unknown
  }> = []

  const defs = (definitions.value ?? []).filter((def: any) => !def?.ui_only && def?.raw && def?.normalized)
  for (const def of defs) {
    const rawKey = def.raw as string
    const rawValue = patientInputFeatures.value?.[rawKey]
    let featureKey: string | undefined

    if (rawKey in byKey) {
      featureKey = rawKey
    } else if (rawValue !== undefined && rawValue !== null) {
      const rawValStr = String(rawValue)
      const exact = `${rawKey}_${rawValStr}`
      if (exact in byKey) {
        featureKey = exact
      } else {
        const lowerVal = rawValStr.toLowerCase()
        featureKey = availableKeys.find((key) => {
          if (!key.startsWith(`${rawKey}_`)) return false
          const suffix = key.slice(rawKey.length + 1).toLowerCase()
          return suffix === lowerVal
        })
      }
    }

    if (!featureKey) continue
    features.push({
      rawKey,
      normalizedKey: def.normalized as string,
      description: def.description,
      section: def.section ?? 'Weitere',
      featureKey,
      importance: byKey[featureKey],
      rawValue
    })
  }

  // Sort: positive factors (descending) first → grouped by section,
  // then negative factors (ascending) → grouped by section.
  features.sort((a, b) => {
    const aPos = a.importance >= 0 ? 0 : 1
    const bPos = b.importance >= 0 ? 0 : 1
    if (aPos !== bPos) return aPos - bPos
    // Within same sign group: sort by section name, then abs importance desc
    const secA = a.section ?? ''
    const secB = b.section ?? ''
    if (secA !== secB) return secA.localeCompare(secB, 'de')
    return Math.abs(b.importance) - Math.abs(a.importance)
  })

  return features
})

const featureImportances = computed(() => matchedFeatures.value.map((f) => f.importance))

// Section boundary annotations for the Plotly chart
const sectionBoundaries = computed(() => {
  const boundaries: Array<{yStart: number; label: string; isPositive: boolean}> = []
  let lastKey = ''
  matchedFeatures.value.forEach((f, i) => {
    const sign = f.importance >= 0 ? '+' : '-'
    const key = `${sign}|${f.section ?? ''}`
    if (key !== lastKey) {
      boundaries.push({
        yStart: i,
        label: (f.importance >= 0 ? '⬆ ' : '⬇ ') + (sections.value?.[f.section ?? ''] ?? f.section ?? (language.value?.startsWith('en') ? 'Other' : 'Weitere')),
        isPositive: f.importance >= 0,
      })
      lastKey = key
    }
  })
  return boundaries
})

// What-if feature list: top N features from SHAP that are adjustable
const whatIfFeatures = computed(() => {
  const defs = definitions.value ?? []
  const defMap = Object.fromEntries(defs.map((d: any) => [d.raw, d]))

  // All SHAP-matched features that are adjustable (options or numeric) – sorted by |importance| descending
  const mapped = matchedFeatures.value.map((f) => {
    const def = defMap[f.rawKey]
    const currentVal = patientInputFeatures.value?.[f.rawKey]
    const label = labelFor(f.normalizedKey, f.rawKey)

    if (def?.input_type === 'number') {
      const numVal = currentVal !== undefined && currentVal !== null ? Number(currentVal) : 0
      return {
        rawKey: f.rawKey,
        normalized: def?.normalized,
        label,
        inputType: 'number' as const,
        options: null,
        sliderMin: 0,
        sliderMax: f.rawKey.toLowerCase().includes('alter') || f.rawKey === 'Alter [J]' ? 100
          : f.rawKey.toLowerCase().includes('dauer') ? 60
          : f.rawKey.toLowerCase().includes('measure') || f.rawKey.toLowerCase().includes('messung') ? 100
          : 50,
        sliderStep: 1,
        defaultVal: numVal,
      }
    }
    if (def?.options?.length > 0) {
      return {
        rawKey: f.rawKey,
        normalized: def?.normalized,
        label,
        inputType: 'select' as const,
        options: (def.options as any[]).map((opt: any) => ({
          title: (opt.labels && (opt.labels.de && i18next.language?.startsWith('de') ? opt.labels.de : opt.labels.en)) ?? opt.value,
          value: opt.value,
        })),
        sliderMin: 0, sliderMax: 1, sliderStep: 1,
        defaultVal: currentVal ?? null,
      }
    }
    return null
  }).filter(Boolean)

  const typed = mapped as Array<{
    rawKey: string; label: string; inputType: string;
    options: Array<{title: string; value: any}> | null;
    sliderMin: number; sliderMax: number; sliderStep: number;
    defaultVal: any;
  }>

  // Remove gender from the controls and prioritise specific features
  return typed
    .filter((item: any) => item.normalized !== 'gender')
    .sort((a: any, b: any) => {
      const preferred = [
        'duration_severe_hl',
        'hearing_loss_onset',
        'hl_operated_ear',
        'imaging_findings_preop',
        'ci_implant_type',
        'age'
      ]
      const ia = preferred.indexOf(a.normalized ?? '')
      const ib = preferred.indexOf(b.normalized ?? '')
      if (ia === -1 && ib === -1) return 0
      if (ia === -1) return 1
      if (ib === -1) return -1
      return ia - ib
    })
})

watch(whatIfFeatures, (feats) => {
  // Initialise whatIfValues from current patient data when features load
  if (feats.length > 0 && Object.keys(whatIfValues.value).length === 0) {
    const init: Record<string, any> = {}
    feats.forEach((f) => { init[f.rawKey] = f.defaultVal })
    whatIfValues.value = init
    // Keep a copy of the initial defaults so we can detect when the user
    // has reverted all changes and clear the modified prediction accordingly.
    initialWhatIfValues.value = { ...init }
  }
})

async function callWhatIf() {
  if (!patient_id.value) return
  whatIfLoading.value = true
  try {
    const res = await fetch(
      `${API_BASE}/api/v1/patients/${encodeURIComponent(patient_id.value)}/predict-override`,
      {
        method: 'POST',
        headers: {'Content-Type': 'application/json', accept: 'application/json'},
        body: JSON.stringify({overrides: whatIfValues.value}),
      }
    )
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    whatIfPrediction.value = data.prediction ?? null
  } catch (e) {
    console.error('what-if failed', e)
  } finally {
    whatIfLoading.value = false
  }
}

function onWhatIfChange() {
  // If overrides exactly match the initial defaults, clear the modified prediction
  const keys = Object.keys(initialWhatIfValues.value)
  let allEqual = true
  for (const k of keys) {
    const a = initialWhatIfValues.value[k]
    const b = whatIfValues.value[k]
    // treat arrays and objects by JSON stringification for simple deep-equality
    if (Array.isArray(a) || typeof a === 'object') {
      if (JSON.stringify(a) !== JSON.stringify(b)) { allEqual = false; break }
    } else {
      if (String(a) !== String(b)) { allEqual = false; break }
    }
  }
  if (allEqual) {
    if (whatIfDebounce) clearTimeout(whatIfDebounce)
    whatIfPrediction.value = null
    whatIfLoading.value = false
    return
  }

  if (whatIfDebounce) clearTimeout(whatIfDebounce)
  whatIfDebounce = setTimeout(() => callWhatIf(), 400)
}

function clearWhatIf(key: string) {
  // Reset this override to the initial default value
  const copy: Record<string, any> = { ...whatIfValues.value }
  if (initialWhatIfValues.value && Object.prototype.hasOwnProperty.call(initialWhatIfValues.value, key)) {
    copy[key] = initialWhatIfValues.value[key]
  } else {
    // Fallback: delete the key
    delete copy[key]
  }
  whatIfValues.value = copy
  // Trigger recalculation / possible reset
  onWhatIfChange()
}

const formatFeatureValue = (value: number) => {
  if (!Number.isFinite(value)) return String(value)
  if (Number.isInteger(value)) return value.toString()
  return value.toFixed(2)
}

const labelFor = (normalized: string, fallback?: string) => {
  return labels.value?.[normalized] ?? fallback ?? normalized
}

const featureLabels = computed(() =>
  matchedFeatures.value.map((feature) => {
    const label = labelFor(feature.normalizedKey, feature.description ?? feature.rawKey)
    const rawDisplay =
      feature.rawValue === undefined || feature.rawValue === null
        ? "—"
        : typeof feature.rawValue === "number"
          ? formatFeatureValue(feature.rawValue)
          : String(feature.rawValue)
    return `${label}  ·  ${rawDisplay}`
  })
)

const explanationPlotHeight = computed(() => {
  const numFeatures = featureLabels.value.length
  if (numFeatures === 0) return 320 // Default height if no features

  const barHeight = 40 // Height per bar in px
  const verticalPadding = 80 // Top and bottom padding for title, labels etc.
  return numFeatures * barHeight + verticalPadding
})

function renderExplanationPlot() {
  if (!explanationPlot.value) return
  if (featureLabels.value.length === 0) {
    Plotly.purge(explanationPlot.value)
    return
  }

  // wrap label into <br>-separated lines
  function wrapLabel(label: string, maxChars = 32) {
    const words = label.split(/\s+/)
    const lines: string[] = []
    let line = ""

    for (const w of words) {
      const next = line ? `${line} ${w}` : w
      if (next.length > maxChars) {
        if (line) lines.push(line)
        line = w
      } else {
        line = next
      }
    }
    if (line) lines.push(line)
    return lines.join("<br>")
  }

  const yVals = featureLabels.value.map((_, i) => i)
  const wrapped = featureLabels.value.map((l) => wrapLabel(l, 44))

  // Split into positive (red) and negative (blue) trace for cleaner legend
  const posIdx = featureImportances.value.map((v, i) => v >= 0 ? i : -1).filter(i => i >= 0)
  const negIdx = featureImportances.value.map((v, i) => v < 0 ? i : -1).filter(i => i >= 0)

  const data: Plotly.Data[] = [
    {
      type: "bar",
      orientation: "h",
      name: language.value?.startsWith('en') ? "⬆ Increases probability" : "⬆ Erhöht Wahrscheinlichkeit",
      x: posIdx.map(i => featureImportances.value[i]),
      y: posIdx.map(i => yVals[i]),
      marker: { color: 'rgba(221, 5, 74, 0.78)', line: { width: 0 } },
      customdata: posIdx.map(i => featureLabels.value[i]),
      hovertemplate: language.value?.startsWith('en') ? "<b>%{customdata}</b><br>Contribution: %{x:.4f}<extra></extra>" : "<b>%{customdata}</b><br>Beitrag: %{x:.4f}<extra></extra>",
      showlegend: true,
    },
    {
      type: "bar",
      orientation: "h",
      name: language.value?.startsWith('en') ? "⬇ Decreases probability" : "⬇ Senkt Wahrscheinlichkeit",
      x: negIdx.map(i => featureImportances.value[i]),
      y: negIdx.map(i => yVals[i]),
      marker: { color: 'rgba(33, 150, 243, 0.78)', line: { width: 0 } },
      customdata: negIdx.map(i => featureLabels.value[i]),
      hovertemplate: language.value?.startsWith('en') ? "<b>%{customdata}</b><br>Contribution: %{x:.4f}<extra></extra>" : "<b>%{customdata}</b><br>Beitrag: %{x:.4f}<extra></extra>",
      showlegend: true,
    },
  ]

  // left-side, wrapped, left-aligned labels
  const annotations: Partial<Plotly.Annotations[number]>[] = wrapped.map((txt, i) => ({
    xref: "paper",
    yref: "y",
    x: 0,
    xanchor: "right",
    xshift: -10,
    y: i,
    text: txt,
    showarrow: false,
    align: "left",
    valign: "middle",
    font: { size: 11, color: '#333' },
  }))

  // Section header annotations on the right side outside chart area
  sectionBoundaries.value.forEach(({ yStart, label, isPositive }) => {
    annotations.push({
      xref: 'paper',
      yref: 'y',
      x: 1.02,
      xanchor: 'left',
      xshift: 0,
      y: yStart,
      text: `<b>${label}</b>`,
      showarrow: false,
      align: 'left',
      valign: 'middle',
      font: { size: 12, color: isPositive ? '#DD054A' : '#2196F3', family: 'Inter, Roboto, system-ui' },
      // Make the label visually distinct: add a lightly shaded background and border
      bgcolor: isPositive ? 'rgba(221,5,74,0.06)' : 'rgba(33,150,243,0.06)',
      bordercolor: isPositive ? '#DD054A' : '#2196F3',
      borderwidth: 1,
      borderpad: 6,
    })
  })

  const layout: Partial<Plotly.Layout> = {
    height: explanationPlotHeight.value,
    xaxis: {
      title: { text: language.value?.startsWith('en') ? "Contribution to prediction" : "Beitrag zur Vorhersage", font: { size: 12, color: '#666' } },
      automargin: true,
      zeroline: true,
      zerolinewidth: 2,
      zerolinecolor: '#999',
      gridcolor: '#eee',
      gridwidth: 1,
    },
    yaxis: {
      showticklabels: false,
      automargin: false,
    },
    legend: {
      orientation: 'h',
      yanchor: 'bottom',
      y: 1.02,
      xanchor: 'left',
      x: 0,
      font: { size: 11 },
    },
    annotations,
    margin: {
      // Dynamic left margin: ~7 px per character of the longest label line,
      // clamped between 240 and 520 px so short labels don't waste space and
      // long labels are never clipped.
      l: Math.max(
        240,
        Math.min(
          520,
          Math.max(...wrapped.map((lbl) =>
            Math.max(...lbl.split('<br>').map((s) => s.replace(/<[^>]+>/g, '').length))
          )) * 7
        )
      ),
      // Dynamic right margin so section header labels are fully visible.
      // Each char ≈ 8 px at font-size 11; add 32 px buffer; min 160, max 280.
      r: sectionBoundaries.value.length
        ? Math.max(160, Math.min(280, Math.max(...sectionBoundaries.value.map((b) => b.label.length)) * 8 + 32))
        : 40,
      t: 10,
      b: 40,
    },
    bargap: 0.28,
  }

  const config: Partial<Plotly.Config> = {
    displayModeBar: false,
    responsive: true,
  }

  Plotly.react(explanationPlot.value, data, layout, config)
}

// Re-render Plotly when labels/values/language change
watch([featureLabels, featureImportances], () => {
  renderExplanationPlot()
})

watch(language, () => {
  void featureDefinitionsStore.loadLabels(language.value)
})

onMounted(async () => {
  // Always start at the top of the page when the prediction view is opened
  window.scrollTo({ top: 0, behavior: 'instant' })

  if (!patient_id.value) {
    await router.replace({name: "NotFound"});
    return;
  }
  if (!definitions.value?.length) {
    await featureDefinitionsStore.loadDefinitions()
  }
  await featureDefinitionsStore.loadLabels(language.value)
  try {
    const thresholdResponse = await fetch(
        `${API_BASE}/api/v1/config/prediction-threshold`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        }
    );

    if (thresholdResponse.ok) {
      const thresholdData = await thresholdResponse.json();
      if (typeof thresholdData?.threshold === "number") {
        threshold.value = thresholdData.threshold;
      }
    } else {
      console.warn("Failed to load prediction threshold");
    }

    const response = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(patient_id.value)}/explainer`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        }
    );

    if (response.status === 404) {
      await router.replace({name: "NotFound"});
      return;
    }
    if (!response.ok) throw new Error("Network error");

    const data = await response.json();
    const rawImportance = data.feature_importance ?? {};
    const rawValues = data.feature_values ?? {};
    const filteredImportance = rawImportance;
    const filteredValues = Object.fromEntries(
      Object.keys(filteredImportance).map((key) => [key, rawValues[key] ?? 0])
    )

    prediction.value = {
      result: data.prediction ?? 0,
      params: filteredImportance,
      feature_values: filteredValues
    };
    predictionWarnings.value = Array.isArray(data.warnings) ? data.warnings : [];
    renderExplanationPlot()

    const response2 = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(patient_id.value)}`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        }
    );

    if (response2.status === 404) {
      await router.replace({name: "NotFound"});
      return;
    }
    if (!response2.ok) throw new Error("Network error");

    const data2 = await response2.json();

    patient_name.value = data2.display_name
    // Store raw birth date; the computed patient_birth_date formats it per locale
    rawBirthDate.value = data2.input_features?.['Geburtsdatum'] ?? null
    patientInputFeatures.value = data2.input_features ?? {}

  } catch (err: any) {
    console.error(err);
    error.value = err?.message ?? "Failed to load patient";
  } finally {
    loading.value = false;
  }
})

onBeforeUnmount(() => {
  i18next.off('languageChanged', onLanguageChanged)
})
</script>

<style scoped>
.prediction-sheet {
  padding: 32px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}

.prediction-value {
  font-size: 56px;
  font-weight: 700;
  line-height: 1;
  margin: 12px 12px 16px 12px;
}

.prediction-status {
  display: inline-block;
  font-size: 14px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 6px;
  margin: 12px 0 16px 0;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Green badge */
.status-success {
  background-color: rgb(var(--v-theme-success));
  color: white;
}

/* Red badge */
.status-error {
  background-color: rgb(var(--v-theme-error));
  color: white;
}

.graph-col {
  display: flex;
  justify-content: flex-end; /* align to the right like in Figma */
}

/* Outer square card */
.graph-sheet {
  border: 1px solid #000; /* black border */
  border-radius: 12px; /* rounded corners */
  padding: 16px;
  width: 100%;
  max-width: 360px; /* tweak to match your layout */
  aspect-ratio: 1 / 1; /* keep it roughly square */
  display: flex;
  flex-direction: column;
}

/* h4-style title */
.graph-title {
  font-weight: 600;
  margin: 0 0 12px 0;
}

/* Inner sheet where the graph will be drawn */
.graph-canvas {
  flex: 1;
  margin-bottom: 12px;
}

/* Caption text under the graph */
.graph-caption {
  line-height: 1.4;
  margin: 0;
}

/* Graph drawing area (empty for now) */
.graph-placeholder {
  flex: 1;
  width: 100%;
  margin-bottom: 12px;
}

/* Thin horizontal gray axis line */
.graph-x-axis {
  width: 100%;
  height: 1px;
  background-color: #d0d0d0; /* light gray like in mockup */
  margin-bottom: 4px;
}

/* 0 --- 100 aligned left/right */
.graph-scale {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-size: 12px;
  color: #666;
  padding: 0 2px;
  margin-bottom: 4px;
}

/* Muted remove button for What-If overrides (less aggressive than error color) */
.whatif-remove-btn {
  color: rgba(0, 0, 0, 0.54);
  min-width: 28px;
  width: 28px;
  height: 28px;
  padding: 0;
}
.whatif-remove-icon {
  color: rgba(0, 0, 0, 0.54);
  opacity: 0.85;
  font-size: 16px;
  line-height: 28px;
}
.whatif-remove-btn:hover .whatif-remove-icon {
  color: rgba(0, 0, 0, 0.8);
  opacity: 1;
}


/* SVG fills area */
.graph-svg {
  width: 100%;
  height: 100%;
}

/* MAIN CURVE – this was missing, so it got filled black */
.graph-curve {
  fill: none; /* 🔥 prevent black wedge */
  stroke: #000;
  stroke-width: 0.7;
}

/* vertical dotted line at patient value */
.graph-patient-line {
  stroke: #bdbdbd;
  stroke-width: 0.4;
  stroke-dasharray: 1.5 1.5;
}

/* blue dot */
.graph-patient-dot {
  fill: rgb(var(--v-theme-primary));
}

/* 'Patient: 87%' label */
.graph-patient-label {
  position: absolute;
  top: 2px;
  color: #000;
}

.label-left {
  left: var(--patient-x-position);
  transform: translateX(-110%); /* shift left by 110% of its own width */
}

.label-right {
  left: var(--patient-x-position);
  transform: translateX(10%); /* shift right by 10% of its own width */
}

.graph-placeholder-relative {
  position: relative;
}

/* axis + scale */
.graph-x-axis {
  width: 100%;
  height: 1px;
  background-color: #d0d0d0;
  margin-bottom: 4px;
}

.graph-scale {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-size: 12px;
  color: #666;
  padding: 0 2px;
  margin-bottom: 4px;
}


</style>
