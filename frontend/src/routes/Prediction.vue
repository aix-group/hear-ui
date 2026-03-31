<template>
  <v-container class="py-8">
    <v-sheet
      :elevation="12"
      border
      class="details-sheet"
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
          <h1 class="prediction-value" :aria-label="$t('prediction.result.probability') + ': ' + (predictionResult * 100).toFixed(0) + '%'">{{ (predictionResult * 100).toFixed(0) }}%</h1>
          <p>{{ $t('prediction.result.probability') }}</p>

          <v-divider
            class="my-2"
          />

          <div
            class="prediction-status"
            role="status"
            :aria-label="recommended ? $t('prediction.result.status.recommended') : $t('prediction.result.status.not_recommended')"
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
          <PredictionGraph
            :predictionResult="predictionResult"
            :recommended="recommended"
            :threshold="threshold"
          />
        </v-col>


      </v-row>
      <v-divider
        class="my-6"
      />

      <!-- Explanations -->
      <v-row justify="start" align="center" no-gutters>
        <v-col cols="12">
          <ExplanationChart
            :matchedFeatures="matchedFeatures"
            :featureLabels="featureLabels"
            :featureImportances="featureImportances"
            :sectionBoundaries="sectionBoundaries"
            :language="language"
          />
        </v-col>
      </v-row>

      <!-- What-If Analysis Panel -->
      <v-row class="mt-2" no-gutters>
        <v-col cols="12">
          <div
            class="whatif-toggle-bar"
            :class="{ 'whatif-toggle-bar--open': whatIfOpen }"
            @click="whatIfOpen = !whatIfOpen"
          >
            <div class="d-flex align-center">
              <v-icon size="20" class="mr-2" color="primary">mdi-flask-outline</v-icon>
              <span class="text-subtitle-2 font-weight-medium">{{ $t('prediction.whatif.toggle') }}</span>
            </div>
            <v-icon size="20" :style="{ transform: whatIfOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.25s ease' }">
              mdi-chevron-down
            </v-icon>
          </div>

            <Transition
              @enter="onAccordionEnter"
              @after-enter="onAccordionAfterEnter"
              @leave="onAccordionLeave"
              @after-leave="onAccordionAfterLeave"
            >
            <div
              v-show="whatIfOpen"
              class="whatif-panel"
            >
              <p class="text-body-2 text-medium-emphasis mb-4">{{ $t('prediction.whatif.description') }}</p>

              <!-- Plausibility warnings -->
              <v-alert
                v-for="(warn, wi) in whatIfPlausibilityWarnings"
                :key="'plaus-' + wi"
                type="warning"
                variant="tonal"
                density="compact"
                class="mb-3"
                icon="mdi-alert-circle-outline"
                border="start"
              >
                {{ warn }}
              </v-alert>

              <div class="whatif-layout">
                <!-- LEFT COLUMN: Feature groups (Accordion) -->
                <div class="whatif-left">
                  <form autocomplete="off" @submit.prevent="">
                    <div
                      v-for="group in whatIfGroups"
                      :key="group.key"
                      class="whatif-group"
                    >
                      <div
                        class="whatif-group-header"
                        @click="toggleGroup(group.key)"
                      >
                        <div class="d-flex align-center">
                          <v-icon size="18" class="mr-2" color="primary">{{ group.icon }}</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">{{ group.title }}</span>
                          <v-chip
                            v-if="groupOverrideCount(group.key) > 0"
                            size="x-small"
                            color="primary"
                            variant="flat"
                            class="ml-2"
                          >
                            {{ groupOverrideCount(group.key) }}
                          </v-chip>
                        </div>
                        <v-icon size="18" :style="{ transform: openGroups[group.key] ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s ease' }">
                          mdi-chevron-down
                        </v-icon>
                      </div>

                        <Transition
                          @enter="onAccordionEnter"
                          @after-enter="onAccordionAfterEnter"
                          @leave="onAccordionLeave"
                          @after-leave="onAccordionAfterLeave"
                        >
                        <div
                          v-show="openGroups[group.key]"
                          class="whatif-group-body"
                        >
                          <div
                            v-for="feat in group.features"
                            :key="feat.rawKey"
                            class="whatif-feature-row"
                            :class="{ 'whatif-feature-row--changed': isOverridden(feat.rawKey) }"
                          >
                            <div class="whatif-feature-top">
                              <div class="whatif-feature-label-row">
                                <v-tooltip
                                  :text="isOverridden(feat.rawKey) ? $t('prediction.whatif.modified_indicator') : ''"
                                  location="top"
                                  :disabled="!isOverridden(feat.rawKey)"
                                >
                                  <template #activator="{ props: tipProps }">
                                    <span
                                      v-bind="tipProps"
                                      class="whatif-dot"
                                      :class="isOverridden(feat.rawKey) ? 'whatif-dot--changed' : 'whatif-dot--default'"
                                    />
                                  </template>
                                </v-tooltip>
                                <span class="whatif-feature-name">{{ feat.label }}</span>
                              </div>
                              <span class="whatif-original-value">{{ formatOriginalValue(feat) }}</span>
                            </div>

                            <!-- Numeric slider (Age) -->
                            <template v-if="feat.inputType === 'number' && feat.normalized === 'age'">
                              <div class="d-flex align-center ga-2 mt-1 whatif-slider-age" style="width:100%;">
                                <v-slider
                                  :key="'age-slider-' + ageSliderMin"
                                  :model-value="ageSliderValue(feat.rawKey)"
                                  :min="ageSliderMin"
                                  :max="ageSliderMax"
                                  :step="feat.sliderStep"
                                  :aria-label="feat.label"
                                  thumb-label="always"
                                  color="primary"
                                  density="default"
                                  hide-details
                                  track-size="8"
                                  thumb-size="24"
                                  style="flex: 1; min-width: 120px;"
                                  @update:model-value="(val: number) => onAgeSliderUpdate(feat.rawKey, val)"
                                />
                                <span class="whatif-slider-val">{{ ageSliderValue(feat.rawKey) }}</span>
                              </div>
                              <!-- Age tooltip warning -->
                              <v-slide-y-transition>
                                <p v-if="ageMinTooltipVisible" class="whatif-age-hint whatif-age-hint--warning">
                                  <v-icon size="14" class="mr-1">mdi-information-outline</v-icon>
                                  {{ $t('prediction.whatif.age_min_tooltip') }}
                                </p>
                              </v-slide-y-transition>
                              <!-- Permanent age hint -->
                              <p class="whatif-age-hint">
                                <v-icon size="14" class="mr-1" color="grey">mdi-information-outline</v-icon>
                                {{ $t('prediction.whatif.age_hint') }}
                              </p>
                            </template>

                            <!-- Numeric slider (non-age) -->
                            <template v-else-if="feat.inputType === 'number'">
                              <div class="d-flex align-center ga-2 mt-1">
                                <v-slider
                                  :model-value="whatIfValues[feat.rawKey]"
                                  :min="feat.sliderMin"
                                  :max="feat.sliderMax"
                                  :step="feat.sliderStep"
                                  :aria-label="feat.label"
                                  thumb-label="always"
                                  color="primary"
                                  density="default"
                                  hide-details
                                  track-size="8"
                                  thumb-size="24"
                                  class="flex-grow-1"
                                  @update:model-value="(val: number) => commitWhatIfChange(feat.rawKey, val)"
                                />
                                <span class="whatif-slider-val">{{ whatIfValues[feat.rawKey] }}</span>
                              </div>
                            </template>

                            <!-- Categorical select -->
                            <template v-else-if="feat.options">
                              <v-select
                                :model-value="whatIfValues[feat.rawKey]"
                                :items="feat.options"
                                item-title="title"
                                item-value="value"
                                :aria-label="feat.label"
                                density="comfortable"
                                variant="outlined"
                                hide-details
                                class="mt-1 whatif-select"
                                @update:model-value="(val: any) => commitWhatIfChange(feat.rawKey, val)"
                              />
                              <!-- Other text field: shown when the selected option is_other -->
                              <v-text-field
                                v-if="feat.otherFieldRaw && feat.options.some((o: any) => o.isOther && o.value === whatIfValues[feat.rawKey])"
                                :model-value="whatIfValues[feat.otherFieldRaw] ?? ''"
                                :aria-label="$t('prediction.whatif.other_specify')"
                                density="comfortable"
                                variant="outlined"
                                hide-details
                                class="mt-2 whatif-other-field"
                                :placeholder="$t('prediction.whatif.other_specify')"
                                @update:model-value="(val: string) => commitWhatIfChange(feat.otherFieldRaw!, val)"
                              />
                            </template>
                          </div>
                        </div>
                        </Transition>
                    </div>
                  </form>
                </div>

                <!-- RIGHT COLUMN: Prediction panel (sticky) -->
                <div class="whatif-right">
                  <div class="whatif-prediction-card">
                    <!-- Bars -->
                    <div class="whatif-bar-section">
                      <div class="whatif-bar-row">
                        <span class="whatif-bar-label">{{ $t('prediction.whatif.original') }}</span>
                        <div class="whatif-bar-track">
                          <div
                            class="whatif-bar-fill whatif-bar-fill--original"
                            :style="{ width: (predictionResult * 100).toFixed(0) + '%' }"
                          />
                        </div>
                        <span class="whatif-bar-value" :class="recommended ? 'text-success' : 'text-error'">
                          {{ (predictionResult * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <div class="whatif-bar-row">
                        <span class="whatif-bar-label">{{ $t('prediction.whatif.modified') }}</span>
                        <div class="whatif-bar-track">
                          <div
                            v-if="whatIfPrediction !== null && !whatIfLoading"
                            class="whatif-bar-fill whatif-bar-fill--modified"
                            :style="{ width: (whatIfPrediction * 100).toFixed(0) + '%' }"
                          />
                        </div>
                        <template v-if="whatIfLoading">
                          <v-progress-circular indeterminate size="18" width="2" color="primary" class="ml-1" />
                        </template>
                        <span v-else-if="whatIfPrediction !== null" class="whatif-bar-value"
                          :class="whatIfPrediction > (threshold ?? 0.5) ? 'text-success' : 'text-error'"
                        >
                          {{ (whatIfPrediction * 100).toFixed(0) }}%
                        </span>
                        <span v-else class="whatif-bar-value text-grey">--</span>
                      </div>
                    </div>

                    <!-- Delta -->
                    <div v-if="whatIfPrediction !== null && !whatIfLoading" class="whatif-delta-section">
                      <span
                        class="whatif-delta-value"
                        :class="whatIfDelta > 0 ? 'whatif-delta--positive' : whatIfDelta < 0 ? 'whatif-delta--negative' : ''"
                      >
                        {{ whatIfDelta > 0 ? '+' : '' }}{{ (whatIfDelta * 100).toFixed(1) }}
                      </span>
                      <span class="whatif-delta-unit">{{ $t('prediction.whatif.percentage_points') }}</span>
                    </div>

                    <!-- SHAP reasoning -->
                    <div v-if="whatIfTopDrivers.length > 0 && !whatIfLoading" class="whatif-shap-section">
                      <p class="whatif-shap-title">{{ $t('prediction.whatif.shap_driven_by') }}</p>
                      <ul class="whatif-shap-list">
                        <li v-for="(driver, idx) in whatIfTopDrivers" :key="idx">{{ driver }}</li>
                      </ul>
                    </div>

                    <!-- Buttons -->
                    <div class="whatif-action-buttons">
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="error"
                        prepend-icon="mdi-refresh"
                        :disabled="!hasAnyOverride"
                        @click="clearAllWhatIf"
                      >
                        {{ $t('prediction.whatif.reset_all') }}
                      </v-btn>
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="grey"
                        prepend-icon="mdi-undo"
                        :disabled="whatIfHistory.length === 0"
                        @click="undoLastWhatIf"
                      >
                        {{ $t('prediction.whatif.undo_last') }}
                      </v-btn>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </Transition>
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
import {API_BASE} from "@/lib/api";
import {logger} from "@/lib/logger";
import i18next from 'i18next'
import FeedbackForm from '@/components/FeedbackForm.vue'
import PredictionGraph from '@/components/PredictionGraph.vue'
import ExplanationChart from '@/components/ExplanationChart.vue'
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
const whatIfHistory = ref<Array<Record<string, any>>>([])
const ageMinTooltipVisible = ref(false)
let ageMinTooltipTimeout: ReturnType<typeof setTimeout> | null = null
let whatIfDebounce: ReturnType<typeof setTimeout> | null = null
const whatIfDelta = computed(() =>
  whatIfPrediction.value !== null ? whatIfPrediction.value - predictionResult.value : 0
)
const hasAnyOverride = computed(() => {
  const keys = Object.keys(initialWhatIfValues.value)
  return keys.some((k) => String(whatIfValues.value[k]) !== String(initialWhatIfValues.value[k]))
})

// Age slider helpers — keep min/max/value always finite so the slider never gets NaN
const ageSliderMin = computed(() => {
  const v = computedPatientAge.value
  return Number.isFinite(v) && v > 0 ? v : 0
})
const ageSliderMax = computed(() => {
  return Math.max(90, ageSliderMin.value + 1)
})
function ageSliderValue(rawKey: string): number {
  const stored = Number(whatIfValues.value[rawKey])
  const min = ageSliderMin.value
  if (Number.isFinite(stored) && stored >= min) return stored
  return min
}

// Plausibility warnings for the what-if panel
const whatIfPlausibilityWarnings = computed<string[]>(() => {
  const warnings: string[] = []
  // Find the age and HL-duration feature keys
  const defs = definitions.value ?? []
  const ageDef = defs.find((d: any) => d.normalized === 'age')
  const hlDurDef = defs.find((d: any) => d.normalized === 'duration_severe_hl')
  if (ageDef && hlDurDef) {
    const ageKey = ageDef.raw as string
    const hlDurKey = hlDurDef.raw as string
    const ageVal = Number(whatIfValues.value[ageKey] ?? 0)
    const hlDurVal = Number(whatIfValues.value[hlDurKey] ?? 0)
    if (hlDurVal > ageVal && ageVal > 0) {
      warnings.push(i18next.t('prediction.whatif.implausible_age_hl'))
    }
  }
  return warnings
})

// Computed patient age for slider min-bound
const computedPatientAge = computed(() => {
  if (rawBirthDate.value) {
    const raw = rawBirthDate.value.trim()
    let birth: Date
    // Handle German DD.MM.YYYY format (new Date() doesn't understand it)
    if (/^\d{2}\.\d{2}\.\d{4}$/.test(raw)) {
      const [dd, mm, yyyy] = raw.split('.')
      birth = new Date(Number(yyyy), Number(mm) - 1, Number(dd))
    } else {
      birth = new Date(raw)
    }
    if (Number.isNaN(birth.getTime())) return 0
    const today = new Date()
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) age--
    return Math.max(0, age)
  }
  return 0
})

// Accordion group open state — all closed by default
const openGroups = ref<Record<string, boolean>>({
  hearing: false,
  symptoms: false,
  imaging: false,
  demographics: false,
  implant: false,
  other: false,
})

function toggleGroup(key: string) {
  openGroups.value = { ...openGroups.value, [key]: !openGroups.value[key] }
}

// Smooth accordion transition helpers (avoid max-height lag)
function onAccordionEnter(el: Element) {
  const e = el as HTMLElement
  e.style.height = '0'
  e.style.opacity = '0'
  e.style.overflow = 'hidden'
  // Force reflow so browser registers the initial 0-height before transitioning
  e.getBoundingClientRect()
  e.style.transition = 'height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease'
  e.style.height = e.scrollHeight + 'px'
  e.style.opacity = '1'
}
function onAccordionAfterEnter(el: Element) {
  const e = el as HTMLElement
  e.style.height = 'auto'
  e.style.overflow = ''
  e.style.transition = ''
  e.style.opacity = ''
}
function onAccordionLeave(el: Element) {
  const e = el as HTMLElement
  e.style.height = e.scrollHeight + 'px'
  e.style.overflow = 'hidden'
  e.style.opacity = '1'
  // Force reflow so the browser registers the explicit height before we transition
  e.getBoundingClientRect()
  e.style.transition = 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease'
  e.style.height = '0'
  e.style.opacity = '0'
}
function onAccordionAfterLeave(el: Element) {
  const e = el as HTMLElement
  e.style.height = ''
  e.style.overflow = ''
  e.style.transition = ''
  e.style.opacity = ''
}

// Group classification for What-If features
function featureGroup(normalized: string): string {
  const hearing = ['hl_operated_ear', 'hearing_loss_onset', 'acquisition_type', 'duration_severe_hl',
    'hearing_disorder_type', 'etiology', 'hl_contra_ear', 'amplification_operated_ear',
    'amplification_contra_ear', 'hearing_loss_start']
  const symptoms = ['tinnitus_preop', 'vertigo_preop', 'otorrhea_preop', 'taste_preop', 'headache_preop']
  const imaging = ['imaging_type_preop', 'imaging_findings_preop']
  const demographics = ['age', 'primary_language', 'german_language_barrier', 'non_verbal',
    'parent_hearing_loss', 'sibling_hearing_loss']
  const implant = ['ci_implant_type', 'pre_measure', 'post12_measure', 'post24_measure', 'interval_days']

  if (hearing.includes(normalized)) return 'hearing'
  if (symptoms.includes(normalized)) return 'symptoms'
  if (imaging.includes(normalized)) return 'imaging'
  if (demographics.includes(normalized)) return 'demographics'
  if (implant.includes(normalized)) return 'implant'
  return 'other'
}

const groupMeta: Record<string, { icon: string; titleKey: string; order: number }> = {
  hearing:      { icon: 'mdi-ear-hearing',        titleKey: 'prediction.whatif.group_hearing',      order: 0 },
  symptoms:     { icon: 'mdi-stethoscope',         titleKey: 'prediction.whatif.group_symptoms',     order: 1 },
  imaging:      { icon: 'mdi-image-filter-hdr',    titleKey: 'prediction.whatif.group_imaging',      order: 2 },
  demographics: { icon: 'mdi-account-outline',     titleKey: 'prediction.whatif.group_demographics', order: 3 },
  implant:      { icon: 'mdi-medical-bag',         titleKey: 'prediction.whatif.group_implant',      order: 4 },
  other:        { icon: 'mdi-dots-horizontal',     titleKey: 'prediction.whatif.group_other',        order: 5 },
}

// Top SHAP drivers for the what-if delta explanation
const whatIfTopDrivers = computed<string[]>(() => {
  if (!hasAnyOverride.value || whatIfPrediction.value === null) return []
  const overriddenKeys = Object.keys(initialWhatIfValues.value).filter((k) =>
    String(whatIfValues.value[k]) !== String(initialWhatIfValues.value[k])
  )
  // Match to feature labels from matchedFeatures
  const drivers: Array<{ label: string; absImp: number }> = []
  for (const feat of matchedFeatures.value) {
    if (overriddenKeys.includes(feat.rawKey)) {
      drivers.push({
        label: labelFor(feat.normalizedKey, feat.rawKey),
        absImp: Math.abs(feat.importance),
      })
    }
  }
  drivers.sort((a, b) => b.absImp - a.absImp)
  return drivers.slice(0, 3).map((d) => d.label)
})

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
const predictionResult = computed(() => prediction.value?.result ?? 0)
const recommended = computed(() => {
  if (threshold.value === null) return false
  return predictionResult.value > threshold.value
})

/* ---------- Plotly Explanations chart ---------- */

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

// Clinical ordering: hearing → demographics → language → imaging → treatment → rest
const whatIfSectionOrder = [
  'hl_operated_ear',
  'hearing_loss_onset',
  'acquisition_type',
  'duration_severe_hl',
  'hearing_disorder_type',
  'etiology',
  'hl_contra_ear',
  'amplification_operated_ear',
  'amplification_contra_ear',
  'age',
  'primary_language',
  'german_language_barrier',
  'imaging_findings_preop',
  'imaging_type_preop',
  'ci_implant_type',
  'pre_measure',
  'post12_measure',
  'post24_measure',
  'tinnitus_preop',
  'vertigo_preop',
  'parent_hearing_loss',
  'sibling_hearing_loss',
]

// What-if feature list: SHAP features that are adjustable, sorted clinically
const whatIfFeatures = computed(() => {
  const lang = language.value?.startsWith('de') ? 'de' : 'en'
  const defs = definitions.value ?? []
  const defMap = Object.fromEntries(defs.map((d: any) => [d.raw, d]))

  const mapped = matchedFeatures.value.map((f) => {
    const def = defMap[f.rawKey]
    const currentVal = patientInputFeatures.value?.[f.rawKey]
    const label = labelFor(f.normalizedKey, f.rawKey)
    const group = featureGroup(def?.normalized ?? '')

    if (def?.input_type === 'number') {
      let numVal = currentVal !== undefined && currentVal !== null ? Number(currentVal) : 0
      // Age: dynamically calculate from birth date so it's always current
      const isAge = def?.normalized === 'age'
      if (isAge && rawBirthDate.value) {
        numVal = computedPatientAge.value
      }
      // sliderMin is always 0 for age so the Vuetify internal calculation never
      // receives model-value < min.  The real lower bound (patient's current age)
      // is applied via a dedicated watcher (see below) and enforced in onAgeSliderUpdate.
      const sliderMin = 0
      const sliderMax = isAge ? 90
        : f.rawKey.toLowerCase().includes('dauer') ? 60
        : f.rawKey.toLowerCase().includes('measure') || f.rawKey.toLowerCase().includes('messung') ? 100
        : 50
      return {
        rawKey: f.rawKey,
        normalized: def?.normalized,
        label,
        group,
        inputType: 'number' as const,
        options: null,
        otherFieldRaw: null as string | null,
        sliderMin,
        sliderMax,
        sliderStep: 1,
        defaultVal: numVal,
      }
    }
    if (def?.options?.length > 0) {
      // Resolve the raw key of the companion "other" text field, if any
      const otherNormalized = def?.other_field as string | undefined
      const otherDef = otherNormalized ? defs.find((d: any) => d.normalized === otherNormalized) : null
      const otherFieldRaw = otherDef?.raw ?? null
      const otherCurrentVal = otherFieldRaw ? (patientInputFeatures.value?.[otherFieldRaw] ?? '') : null
      return {
        rawKey: f.rawKey,
        normalized: def?.normalized,
        label,
        group,
        inputType: 'select' as const,
        options: (() => {
          let seenOther = false
          return (def.options as any[]).reduce((acc: any[], opt: any) => {
            if (opt.is_other) {
              if (seenOther) return acc  // deduplicate – skip extra is_other options
              seenOther = true
              acc.push({
                title: lang === 'de' ? 'Andere' : 'Other',
                value: opt.value,
                isOther: true,
              })
            } else {
              acc.push({
                title: (opt.labels && (lang === 'de' && opt.labels.de ? opt.labels.de : opt.labels.en)) ?? opt.value,
                value: opt.value,
                isOther: false,
              })
            }
            return acc
          }, [])
        })(),
        otherFieldRaw,
        otherFieldDefaultVal: otherCurrentVal,
        sliderMin: 0, sliderMax: 1, sliderStep: 1,
        defaultVal: currentVal ?? null,
      }
    }
    return null
  }).filter(Boolean)

  const typed = mapped as Array<{
    rawKey: string; label: string; group: string; inputType: string;
    options: Array<{title: string; value: any; isOther?: boolean}> | null;
    otherFieldRaw: string | null;
    otherFieldDefaultVal?: any;
    sliderMin: number; sliderMax: number; sliderStep: number;
    defaultVal: any; normalized?: string;
  }>

  return typed
    .filter((item: any) => item.normalized !== 'gender')
    .sort((a: any, b: any) => {
      const ia = whatIfSectionOrder.indexOf(a.normalized ?? '')
      const ib = whatIfSectionOrder.indexOf(b.normalized ?? '')
      if (ia === -1 && ib === -1) return 0
      if (ia === -1) return 1
      if (ib === -1) return -1
      return ia - ib
    })
})

// Grouped features for the accordion
const whatIfGroups = computed(() => {
  const feats = whatIfFeatures.value
  const grouped: Record<string, typeof feats> = {}
  for (const f of feats) {
    const g = (f as any).group ?? 'other'
    if (!grouped[g]) grouped[g] = []
    grouped[g].push(f)
  }

  return Object.entries(grouped)
    .map(([key, features]) => ({
      key,
      icon: groupMeta[key]?.icon ?? 'mdi-dots-horizontal',
      title: i18next.t(groupMeta[key]?.titleKey ?? 'prediction.whatif.group_other'),
      order: groupMeta[key]?.order ?? 99,
      features,
    }))
    .sort((a, b) => a.order - b.order)
})

function groupOverrideCount(groupKey: string): number {
  const group = whatIfGroups.value.find((g) => g.key === groupKey)
  if (!group) return 0
  return group.features.filter((f) => isOverridden(f.rawKey)).length
}

function formatOriginalValue(feat: any): string {
  const val = initialWhatIfValues.value?.[feat.rawKey]
  if (val === undefined || val === null) return '--'
  let display: string
  if (feat.inputType === 'number') {
    display = String(val)
  } else {
    // Resolve localized label for categorical
    const opt = feat.options?.find((o: any) => String(o.value) === String(val))
    display = opt?.title ?? String(val)
  }
  return i18next.t('prediction.whatif.original_value', { value: display })
}

// When the patient's birth date loads (second API call), immediately sync the
// age value in whatIfValues so the slider never renders with value < its min.
watch(computedPatientAge, (age) => {
  if (age <= 0) return
  const defs = definitions.value ?? []
  const ageDef = defs.find((d: any) => d.normalized === 'age')
  if (!ageDef) return
  const ageKey = ageDef.raw as string
  const stored = Number(whatIfValues.value[ageKey] ?? 0)
  const initStored = Number(initialWhatIfValues.value[ageKey] ?? 0)
  // Update if stored value is below the new min age, or if user hasn't manually changed it
  if (stored < age || stored === initStored) {
    whatIfValues.value = { ...whatIfValues.value, [ageKey]: age }
    initialWhatIfValues.value = { ...initialWhatIfValues.value, [ageKey]: age }
  }
}, { immediate: true })

// Cancel pending debounce and reset loading state when the panel is closed
watch(whatIfOpen, (open) => {
  if (!open) {
    if (whatIfDebounce) clearTimeout(whatIfDebounce)
    whatIfLoading.value = false
  }
})

watch(whatIfFeatures, (feats) => {
  if (feats.length === 0) return

  if (Object.keys(whatIfValues.value).length === 0) {
    // First initialization: set all values from patient data defaults
    const init: Record<string, any> = {}
    feats.forEach((f) => {
      init[f.rawKey] = f.defaultVal
      // Also initialize companion other-text field if present
      if ((f as any).otherFieldRaw) {
        const otherKey = (f as any).otherFieldRaw as string
        init[otherKey] = (f as any).otherFieldDefaultVal ?? ''
      }
    })
    whatIfValues.value = init
    initialWhatIfValues.value = { ...init }
  } else {
    // Patient data just finished loading: fix stale numeric values
    for (const f of feats) {
      if (f.inputType !== 'number') continue
      const stored = whatIfValues.value[f.rawKey]
      const initStored = initialWhatIfValues.value[f.rawKey]
      const isUserUnchanged = String(stored) === String(initStored)
      // Update if value is missing, NaN, or still 0 while a real default exists
      if (isUserUnchanged && (stored === undefined || stored === null || Number.isNaN(Number(stored)) || (Number(stored) === 0 && f.defaultVal > 0))) {
        whatIfValues.value = { ...whatIfValues.value, [f.rawKey]: f.defaultVal }
        initialWhatIfValues.value = { ...initialWhatIfValues.value, [f.rawKey]: f.defaultVal }
      }
      // Also initialize other-text field if not yet present
      if ((f as any).otherFieldRaw) {
        const otherKey = (f as any).otherFieldRaw as string
        if (!(otherKey in whatIfValues.value)) {
          whatIfValues.value = { ...whatIfValues.value, [otherKey]: (f as any).otherFieldDefaultVal ?? '' }
          initialWhatIfValues.value = { ...initialWhatIfValues.value, [otherKey]: (f as any).otherFieldDefaultVal ?? '' }
        }
      }
    }
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
  } catch {
    // what-if error silently ignored; UI shows original prediction
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

// Wrapper used by sliders/selects: saves a snapshot BEFORE the value is applied,
// then triggers re-calculation.
function commitWhatIfChange(key: string, val: any) {
  whatIfHistory.value.push(JSON.parse(JSON.stringify(whatIfValues.value)))
  whatIfValues.value = { ...whatIfValues.value, [key]: val }
  onWhatIfChange()
}

function undoLastWhatIf() {
  if (whatIfHistory.value.length === 0) return
  const prev = whatIfHistory.value.pop()!
  whatIfValues.value = prev
  onWhatIfChange()
}

function isOverridden(key: string): boolean {
  if (!initialWhatIfValues.value) return false
  return whatIfValues.value[key] !== initialWhatIfValues.value[key]
}

function clearAllWhatIf() {
  whatIfHistory.value.push(JSON.parse(JSON.stringify(whatIfValues.value)))
  if (initialWhatIfValues.value && Object.keys(initialWhatIfValues.value).length > 0) {
    whatIfValues.value = { ...initialWhatIfValues.value }
  } else {
    whatIfValues.value = {}
  }
  onWhatIfChange()
}

// Age slider: enforce min = patient's current age, bounce back with tooltip
function onAgeSliderUpdate(rawKey: string, val: number) {
  const minAge = computedPatientAge.value
  if (!Number.isFinite(val)) return
  // Clamp value to at least the patient's current age
  const clamped = minAge > 0 ? Math.max(val, minAge) : val
  if (clamped !== val) {
    whatIfValues.value = { ...whatIfValues.value, [rawKey]: clamped }
    ageMinTooltipVisible.value = true
    if (ageMinTooltipTimeout) clearTimeout(ageMinTooltipTimeout)
    ageMinTooltipTimeout = setTimeout(() => { ageMinTooltipVisible.value = false }, 3000)
    return
  }
  commitWhatIfChange(rawKey, clamped)
}

const formatFeatureValue = (value: number) => {
  if (!Number.isFinite(value)) return String(value)
  if (Number.isInteger(value)) return value.toString()
  return value.toFixed(2)
}

const labelFor = (normalized: string, fallback?: string) => {
  return labels.value?.[normalized] ?? fallback ?? normalized
}

const featureLabels = computed(() => {
  const lang = language.value?.startsWith('de') ? 'de' : 'en'
  const defMap = Object.fromEntries((definitions.value ?? []).map((d: any) => [d.raw, d]))
  return matchedFeatures.value.map((feature) => {
    const label = labelFor(feature.normalizedKey, feature.description ?? feature.rawKey)
    let rawDisplay: string
    if (feature.rawValue === undefined || feature.rawValue === null) {
      rawDisplay = "—"
    } else if (typeof feature.rawValue === "number") {
      rawDisplay = formatFeatureValue(feature.rawValue)
    } else {
      // Try to resolve localized option label
      const def = defMap[feature.rawKey]
      const rawStr = String(feature.rawValue)
      const option = def?.options?.find((o: any) => String(o.value) === rawStr)
      rawDisplay = option?.labels?.[lang] ?? option?.labels?.['en'] ?? rawStr
    }
    return `${label}  ·  ${rawDisplay}`
  })
})

// Re-render chart when labels/values/language change (handled by ExplanationChart component via watch)

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
      logger.warn("Failed to load prediction threshold");
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
    // ExplanationChart re-renders reactively via its own watchers

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

  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : "Failed to load patient";
  } finally {
    loading.value = false;
  }
})

onBeforeUnmount(() => {
  i18next.off('languageChanged', onLanguageChanged)
  if (whatIfDebounce) clearTimeout(whatIfDebounce)
  if (ageMinTooltipTimeout) clearTimeout(ageMinTooltipTimeout)
})
</script>

<style scoped>
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

/* What-If toggle bar */
.whatif-toggle-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.10);
  cursor: pointer;
  transition: background 200ms ease, border-color 200ms ease;
  user-select: none;
}
.whatif-toggle-bar:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.20);
}
.whatif-toggle-bar--open {
  border-radius: 10px 10px 0 0;
  border-bottom-color: transparent;
}

/* What-If panel body */
.whatif-panel {
  background: rgba(var(--v-theme-primary), 0.02);
  border: 1px solid rgba(var(--v-theme-primary), 0.10);
  border-top: none;
  border-radius: 0 0 10px 10px;
  padding: 20px;
  overflow: hidden;
}

/* What-If two-column layout */
.whatif-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}
.whatif-left {
  min-width: 0;
}
.whatif-right {
  position: sticky;
  top: 80px;
}

/* Prediction card (right panel) */
.whatif-prediction-card {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* Probability bars */
.whatif-bar-track {
  height: 10px;
  border-radius: 5px;
  background: #eee;
  overflow: hidden;
}
.whatif-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 400ms ease;
}
.whatif-bar-fill--original {
  background: #2A6FDB;
}
.whatif-bar-fill--modified {
  background: #2ECC71;
}

/* Delta chip */
.whatif-delta-positive {
  color: #2ECC71;
  font-weight: 600;
}
.whatif-delta-negative {
  color: #e74c3c;
  font-weight: 600;
}
.whatif-delta-neutral {
  color: #90a4ae;
  font-weight: 600;
}

/* SHAP reasoning list */
.whatif-shap-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.whatif-shap-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 0.82rem;
  color: rgba(0,0,0,0.7);
}

/* Accordion group headers */
.whatif-group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(0,0,0,0.02);
  border: 1px solid rgba(0,0,0,0.06);
  transition: background 150ms;
  user-select: none;
}
.whatif-group-header:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}
.whatif-group-title {
  font-weight: 600;
  font-size: 0.9rem;
  flex: 1;
}
.whatif-group-badge {
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  border-radius: 12px;
  padding: 1px 8px;
  font-size: 0.72rem;
  font-weight: 600;
}

/* Feature rows inside groups */
.whatif-feature-row:last-child {
  border-bottom: none;
}
.whatif-feature-row:hover {
  background: rgba(0,0,0,0.015);
}
.whatif-feature-label {
  display: flex;
  align-items: center;
  color: rgba(0, 0, 0, 0.65);
  font-size: 0.82rem;
  min-width: 180px;
  flex-shrink: 0;
}
.whatif-feature-control {
  flex: 1;
  min-width: 200px;
}
.whatif-feature-original {
  font-size: 0.72rem;
  color: rgba(0,0,0,0.4);
  white-space: nowrap;
}

/* Change indicator dot */
.whatif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 200ms;
}
.whatif-dot--active {
  opacity: 1;
}

/* Select styling */
.whatif-select :deep(.v-field) {
  font-size: 1.05rem;
  min-height: 64px;
  padding: 10px 16px;
  height: auto !important;
}
.whatif-select :deep(.v-field__input) {
  min-height: 52px;
  height: auto !important;
  font-size: 1.05rem;
  flex-wrap: wrap !important;
  overflow: visible !important;
}
.whatif-select :deep(.v-select__selection) {
  font-size: 1.05rem;
  white-space: normal !important;
  word-break: break-word !important;
  overflow: visible !important;
  text-overflow: unset !important;
  max-width: 100% !important;
  line-height: 1.5;
  font-weight: 500;
}
.whatif-select :deep(.v-select__selection-text) {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
}
.whatif-select :deep(.v-overlay__content) {
  min-width: 300px !important;
}
.whatif-select :deep(.v-list-item-title) {
  white-space: normal !important;
  word-break: break-word;
  line-height: 1.5;
  font-size: 1.05rem;
  padding: 4px 0;
}
.whatif-select :deep(.v-list-item) {
  min-height: 48px;
  padding: 8px 16px;
}

/* Responsive: stack on mobile */
@media (max-width: 960px) {
  .whatif-layout {
    grid-template-columns: 1fr;
  }
  .whatif-right {
    position: sticky;
    top: 0;
    z-index: 2;
    order: -1;
  }
  .whatif-feature-row {
    flex-wrap: wrap;
  }
  .whatif-feature-label {
    min-width: 100%;
  }
}

/* Group body (accordion content) */
.whatif-group-body {
  overflow: hidden;
  padding: 4px 0 8px;
}
.whatif-group {
  margin-bottom: 8px;
}

/* Feature row inner layout */
.whatif-feature-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.whatif-feature-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.whatif-feature-name {
  font-size: 0.82rem;
  color: rgba(0,0,0,0.72);
  font-weight: 500;
}
.whatif-original-value {
  font-size: 0.72rem;
  color: rgba(0,0,0,0.38);
  white-space: nowrap;
}
.whatif-slider-val {
  min-width: 40px;
  text-align: right;
  font-size: 0.95rem;
  font-weight: 700;
  color: rgba(0,0,0,0.8);
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 6px;
  padding: 2px 8px;
}

/* Age slider: full-width, taller track and thumb for precise selection */
.whatif-slider-age {
  min-height: 64px;
  width: 100%;
  touch-action: none;
}
.whatif-slider-age :deep(.v-input) {
  width: 100%;
}
.whatif-slider-age :deep(.v-slider) {
  touch-action: none;
}
.whatif-slider-age :deep(.v-slider-track),
.whatif-slider-age :deep(.v-slider-thumb) {
  pointer-events: auto !important;
  touch-action: none;
}
.whatif-slider-age :deep(.v-slider-track__background),
.whatif-slider-age :deep(.v-slider-track__fill) {
  height: 14px !important;
  border-radius: 7px;
}
.whatif-slider-age :deep(.v-slider-thumb__surface) {
  width: 32px !important;
  height: 32px !important;
}

/* All sliders: larger overall */
.whatif-feature-control :deep(.v-slider-track__background),
.whatif-feature-control :deep(.v-slider-track__fill) {
  height: 10px !important;
  border-radius: 5px;
}
.whatif-feature-control :deep(.v-slider-thumb__surface) {
  width: 26px !important;
  height: 26px !important;
}
.whatif-feature-row--changed {
  background: rgba(var(--v-theme-primary), 0.03);
}

/* Change indicator dot variants */
.whatif-dot--changed {
  opacity: 1;
  background: rgb(var(--v-theme-primary));
}
.whatif-dot--default {
  opacity: 0.2;
  background: #bdbdbd;
}

/* Bar section layout */
.whatif-bar-section {
  margin-bottom: 16px;
}
.whatif-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.whatif-bar-label {
  font-size: 0.72rem;
  color: rgba(0,0,0,0.5);
  min-width: 60px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.whatif-bar-value {
  font-size: 1.1rem;
  font-weight: 700;
  min-width: 40px;
  text-align: right;
}

/* Delta section */
.whatif-delta-section {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 0;
  border-top: 1px solid rgba(0,0,0,0.06);
  margin-top: 4px;
}
.whatif-delta-value {
  font-size: 1.3rem;
  font-weight: 700;
}
.whatif-delta--positive {
  color: #2ECC71;
}
.whatif-delta--negative {
  color: #e74c3c;
}
.whatif-delta-unit {
  font-size: 0.75rem;
  color: rgba(0,0,0,0.45);
}

/* SHAP section */
.whatif-shap-section {
  padding: 10px 0 4px;
  border-top: 1px solid rgba(0,0,0,0.06);
}
.whatif-shap-title {
  font-size: 0.75rem;
  color: rgba(0,0,0,0.5);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 4px;
}

/* Action buttons */
.whatif-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.06);
  margin-top: 8px;
}
.whatif-action-buttons .v-btn {
  min-width: 0;
  flex-shrink: 1;
}

/* Other-text input */
.whatif-other-field :deep(.v-field) {
  font-size: 0.9rem;
}

/* Age hint under slider */
.whatif-age-hint {
  display: flex;
  align-items: center;
  font-size: 0.72rem;
  color: rgba(0,0,0,0.45);
  margin: 4px 0 0 2px;
  line-height: 1.4;
}
.whatif-age-hint--warning {
  color: #e65100;
  font-weight: 500;
}

/* SHAP list bullets */
.whatif-shap-list li {
  padding: 2px 0;
  font-size: 0.82rem;
  color: rgba(0,0,0,0.7);
}
.whatif-shap-list li::before {
  content: '– ';
  color: rgba(0,0,0,0.4);
}

/* Feature row: flex-direction column so original value + control stack below the label row */
.whatif-feature-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 14px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  transition: background 150ms;
}


</style>
