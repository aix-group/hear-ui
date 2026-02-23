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

const route = useRoute()
const router = useRouter()
const patient_name = ref("")
const patient_birth_date = ref<string | null>(null)
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

if (!patient_id.value) {
  router.replace({name: "NotFound"})
}

const language = ref(i18next.language)
const onLanguageChanged = (lng: string) => {
  language.value = lng
}
i18next.on('languageChanged', onLanguageChanged)
const {definitions, labels} = useFeatureDefinitions()

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

  // Sort: positive factors (descending by importance) first, then negative (ascending by importance)
  features.sort((a, b) => {
    const aPos = a.importance >= 0 ? 0 : 1
    const bPos = b.importance >= 0 ? 0 : 1
    if (aPos !== bPos) return aPos - bPos
    // Within same sign group, sort by absolute importance descending
    return Math.abs(b.importance) - Math.abs(a.importance)
  })

  return features
})

const featureImportances = computed(() => matchedFeatures.value.map((f) => f.importance))

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
    const sectionLabel = feature.section ? `[${feature.section}] ` : ''
    return `${sectionLabel}${label}: ${rawDisplay}`
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
  const wrapped = featureLabels.value.map((l) => wrapLabel(l, 48))

  const data: Plotly.Data[] = [
    {
      type: "bar",
      orientation: "h",
      x: featureImportances.value,
      y: yVals,
      marker: {
        color: featureImportances.value.map((v) => (v >= 0 ? "#DD054A" : "#2196F3")),
      },
      // show full unwrapped label on hover
      customdata: featureLabels.value,
      hovertemplate: "<b>%{customdata}</b><br>Contribution: %{x:.4f}<extra></extra>",
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
    font: { size: 11 },
  }))

  const layout: Partial<Plotly.Layout> = {
    height: explanationPlotHeight.value, // uses your computed height
    xaxis: {
      title: "Contribution to prediction",
      automargin: true,
      zeroline: true,
      zerolinewidth: 1,
    },
    yaxis: {
      showticklabels: false, // IMPORTANT: no tick labels
      automargin: false,
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
      r: 24,
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
    // Extract and format birth date for display
    const rawBirthDate = data2.input_features?.['Geburtsdatum'] ?? null
    if (rawBirthDate) {
      // Convert YYYY-MM-DD to DD.MM.YYYY if needed
      if (/^\d{4}-\d{2}-\d{2}$/.test(rawBirthDate)) {
        const [y, m, d] = rawBirthDate.split('-')
        patient_birth_date.value = `${d}.${m}.${y}`
      } else {
        patient_birth_date.value = rawBirthDate
      }
    }
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
