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
        <h1>{{ $t('predictions_home.title') }}</h1>
      </v-row>

      <v-divider class="my-6"/>



      <!-- Action Buttons -->
      <div class="d-flex justify-center ga-3 mt-6">
        <v-btn
            :to="{ name: 'SearchPatients' }"
            color="grey-darken-1"
            prepend-icon="mdi-magnify"
            size="small"
            variant="tonal"
            density="comfortable"
        >
          {{ $t('predictions_home.action_cards.search_patients.title') }}
        </v-btn>
        <v-btn
            :to="{ name: 'CreatePatient' }"
            color="grey-darken-1"
            size="small"
            variant="tonal"
            density="comfortable"
            prepend-icon="mdi-account-plus"
        >
          {{ $t('predictions_home.action_cards.create_patient.title') }}
        </v-btn>
      </div>

      <v-divider class="my-4 mb-6"/>

      <!-- Model Card Section -->
      <v-row>
        <v-col>
          <v-card class="mc-pro" elevation="4">

            <!-- ── Gradient Header ── -->
            <div class="mc-header pa-6 text-white">
              <div class="d-flex flex-wrap align-center ga-3 mb-1">
                <v-icon size="26">mdi-clipboard-text-outline</v-icon>
                <span class="text-h5 font-weight-bold" style="letter-spacing:.01em">{{ cardData?.name }}</span>
                <v-chip variant="outlined" color="white" size="small" class="font-weight-medium">
                  {{ cardData?.version }}
                </v-chip>
                <v-chip :color="cardData?.status === 'active' || cardData?.status === 'aktiv' ? '#81c784' : '#ffb74d'" size="small" class="font-weight-bold text-uppercase">
                  {{ cardData?.status ?? $t('predictions_home.model_cards.status_active') }}
                </v-chip>
              </div>
              <div class="text-body-2" style="opacity:.8">
                {{ cardData?.model_type }} &middot; {{ $t('predictions_home.model_cards.deployed') }}: {{ cardData?.deployment_date }}
              </div>
            </div>

            <!-- ── Quick-Stats Bar ── -->
            <div class="mc-stats bg-grey-lighten-4 pa-4">
              <v-row dense>
                <v-col cols="6" sm="3">
                  <div class="stat-cell">
                    <v-icon color="primary" size="20" class="mb-1">mdi-account-group</v-icon>
                    <div class="stat-val">{{ cardData?.training?.dataset_size }}</div>
                    <div class="stat-lbl">{{ $t('predictions_home.model_cards.stats.patients') }}</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="stat-cell">
                    <v-icon color="primary" size="20" class="mb-1">mdi-tag-multiple-outline</v-icon>
                    <div class="stat-val">{{ cardData?.training?.features_count }}</div>
                    <div class="stat-lbl">{{ $t('predictions_home.model_cards.stats.features') }}</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="stat-cell">
                    <v-icon color="primary" size="20" class="mb-1">mdi-calendar-check-outline</v-icon>
                    <div class="stat-val">{{ cardData?.training?.training_date }}</div>
                    <div class="stat-lbl">{{ $t('predictions_home.model_cards.stats.training_date') }}</div>
                  </div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="stat-cell">
                    <v-icon color="primary" size="20" class="mb-1">mdi-sync</v-icon>
                    <div class="stat-val stat-val--sm">{{ cardData?.training?.validation_strategy }}</div>
                    <div class="stat-lbl">{{ $t('predictions_home.model_cards.stats.validation') }}</div>
                  </div>
                </v-col>
              </v-row>
            </div>

            <v-card-text class="pa-6">
              <!-- Loading -->
              <div v-if="loading" class="text-center py-12">
                <v-progress-circular indeterminate color="primary" size="64"/>
                <p class="mt-4 text-grey">{{ $t('predictions_home.model_cards.loading') }}</p>
              </div>

              <!-- Error -->
              <div v-else-if="error" class="text-center py-12">
                <v-icon color="error" size="64">mdi-alert-circle-outline</v-icon>
                <p class="mt-4 text-error">{{ error }}</p>
                <v-btn @click="loadModelCard" variant="outlined" color="primary" class="mt-4">{{ $t('predictions_home.model_cards.retry') }}</v-btn>
              </div>

              <template v-else-if="cardData">

                <!-- ── Performance Metrics ── -->
                <div class="mc-section-title mb-3">
                  <v-icon size="17" class="mr-1">mdi-chart-bar</v-icon>
                  {{ $t('predictions_home.model_cards.performance_title') }}
                </div>
                <v-row dense class="mb-5">
                  <v-col cols="12" sm="6">
                    <div class="metric-card">
                      <div class="d-flex justify-space-between align-end mb-1">
                        <span class="metric-label">{{ $t('predictions_home.model_cards.metrics.accuracy') }}</span>
                        <span class="metric-value">{{ (cardData.metrics.test_set.accuracy * 100).toFixed(0) }}%</span>
                      </div>
                      <v-progress-linear :model-value="cardData.metrics.test_set.accuracy * 100" color="primary" rounded height="10" bg-color="rgba(0,0,0,0.07)"/>
                    </div>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <div class="metric-card">
                      <div class="d-flex justify-space-between align-end mb-1">
                        <span class="metric-label">{{ $t('predictions_home.model_cards.metrics.f1') }}</span>
                        <span class="metric-value">{{ cardData.metrics.test_set.f1_score.toFixed(2) }}</span>
                      </div>
                      <v-progress-linear :model-value="cardData.metrics.test_set.f1_score * 100" color="secondary" rounded height="10" bg-color="rgba(0,0,0,0.07)"/>
                    </div>
                  </v-col>
                </v-row>
                <v-alert type="info" variant="tonal" density="compact" class="text-caption mb-6">
                  {{ $t('predictions_home.model_cards.metrics_hint') }}
                </v-alert>

                <!-- ── Hyperparameter Chips ── -->
                <div class="mc-section-title mb-1">
                  <v-icon size="17" class="mr-1">mdi-tune-variant</v-icon>
                  {{ $t('predictions_home.model_cards.hyperparameters.title') }}
                </div>
                <div class="hp-grid mb-7">
                  <div
                    v-for="hp in hyperparamsToShow"
                    :key="hp.key"
                    class="hp-card pa-3"
                  >
                    <div class="d-flex align-center justify-space-between ga-2 mb-1">
                      <span class="hp-label">{{ hp.label }}</span>
                      <v-chip size="x-small" variant="tonal" color="primary" class="font-weight-bold">{{ hp.value }}</v-chip>
                    </div>
                    <div class="hp-desc">{{ hp.desc }}</div>
                  </div>
                </div>

                <!-- ── Tabbed Sections ── -->
                <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-1">
                  <v-tab value="use">
                    <v-icon start size="16">mdi-check-circle-outline</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.use') }}
                  </v-tab>
                  <v-tab value="limits">
                    <v-icon start size="16">mdi-alert-outline</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.limits') }}
                  </v-tab>
                  <v-tab value="recs">
                    <v-icon start size="16">mdi-lightbulb-outline</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.recs') }}
                  </v-tab>
                  <v-tab value="ethics">
                    <v-icon start size="16">mdi-scale-balance</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.ethics') }}
                  </v-tab>
                  <v-tab value="features">
                    <v-icon start size="16">mdi-format-list-checks</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.features') }}
                  </v-tab>
                  <v-tab value="xai">
                    <v-icon start size="16">mdi-brain</v-icon>
                    {{ $t('predictions_home.model_cards.tabs.xai') }}
                  </v-tab>
                </v-tabs>
                <v-divider class="mb-4"/>

                <v-window v-model="activeTab">

                  <!-- Intended Use -->
                  <v-window-item value="use">
                    <div class="mc-subsection-title mb-2">{{ $t('predictions_home.model_cards.intended_use_title') }}</div>
                    <v-list density="compact" class="mb-5 mc-list mc-list--ok">
                      <v-list-item
                        v-for="(item, i) in cardData.intended_use"
                        :key="i"
                        prepend-icon="mdi-check-circle-outline"
                        :title="item"
                        class="mc-list-item"
                      />
                    </v-list>
                    <div class="mc-subsection-title mc-subsection-title--warn mb-2">{{ $t('predictions_home.model_cards.not_intended_title') }}</div>
                    <v-list density="compact" class="mc-list mc-list--warn">
                      <v-list-item
                        v-for="(item, i) in cardData.not_intended_for"
                        :key="i"
                        prepend-icon="mdi-close-circle-outline"
                        :title="item"
                        class="mc-list-item"
                      />
                    </v-list>
                  </v-window-item>

                  <!-- Limitations -->
                  <v-window-item value="limits">
                    <v-list density="compact" class="mc-list mc-list--warn">
                      <v-list-item
                        v-for="(item, i) in cardData.limitations"
                        :key="i"
                        prepend-icon="mdi-alert-circle-outline"
                        :title="item"
                        class="mc-list-item"
                      />
                    </v-list>
                  </v-window-item>

                  <!-- Recommendations -->
                  <v-window-item value="recs">
                    <v-list density="compact" class="mc-list mc-list--ok">
                      <v-list-item
                        v-for="(item, i) in cardData.recommendations"
                        :key="i"
                        prepend-icon="mdi-lightbulb-on-outline"
                        :title="item"
                        class="mc-list-item"
                      />
                    </v-list>
                  </v-window-item>

                  <!-- Ethics -->
                  <v-window-item value="ethics">
                    <v-list density="compact" class="mc-list">
                      <v-list-item
                        prepend-icon="mdi-scale-balance"
                        class="mc-list-item mc-ethics-item"
                      >
                        <template #title><span class="font-weight-bold">{{ $t('predictions_home.model_cards.ethics_labels.fairness') }}</span></template>
                        <template #subtitle><span class="text-body-2">{{ cardData.ethical_considerations.fairness }}</span></template>
                      </v-list-item>
                      <v-divider class="my-2"/>
                      <v-list-item
                        prepend-icon="mdi-shield-account-outline"
                        class="mc-list-item mc-ethics-item"
                      >
                        <template #title><span class="font-weight-bold">{{ $t('predictions_home.model_cards.ethics_labels.privacy') }}</span></template>
                        <template #subtitle><span class="text-body-2">{{ cardData.ethical_considerations.privacy }}</span></template>
                      </v-list-item>
                      <v-divider class="my-2"/>
                      <v-list-item
                        prepend-icon="mdi-eye-outline"
                        class="mc-list-item mc-ethics-item"
                      >
                        <template #title><span class="font-weight-bold">{{ $t('predictions_home.model_cards.ethics_labels.transparency') }}</span></template>
                        <template #subtitle><span class="text-body-2">{{ cardData.ethical_considerations.transparency }}</span></template>
                      </v-list-item>
                    </v-list>
                  </v-window-item>

                  <!-- Features -->
                  <v-window-item value="features">
                    <v-chip variant="tonal" color="secondary" size="small" class="font-weight-bold mb-4">
                      {{ $t('predictions_home.model_cards.features.total', { count: cardData.features_total || cardData.training?.features_count }) }}
                    </v-chip>
                    <div v-if="cardData.feature_groups" class="feature-groups mt-2">
                      <div
                        v-for="(feats, groupName) in cardData.feature_groups"
                        :key="groupName"
                        class="feature-group mb-4"
                      >
                        <div class="feature-group-title mb-2">{{ groupName }}</div>
                        <div class="d-flex flex-wrap ga-1">
                          <v-chip
                            v-for="(feat, idx) in feats"
                            :key="idx"
                            variant="outlined"
                            size="small"
                            color="primary"
                            class="feature-chip"
                          >
                            {{ feat }}
                          </v-chip>
                        </div>
                      </div>
                    </div>
                  </v-window-item>

                  <!-- XAI -->
                  <v-window-item value="xai">
                    <v-list density="compact" class="mc-list mc-list--ok">
                      <v-list-item prepend-icon="mdi-chart-waterfall" class="mc-list-item">
                        <template #title><span class="text-body-2">{{ $t('predictions_home.model_cards.xai.shap') }}</span></template>
                      </v-list-item>
                      <v-list-item prepend-icon="mdi-star-outline" class="mc-list-item">
                        <template #title><span class="text-body-2">{{ $t('predictions_home.model_cards.xai.important_factors') }}</span></template>
                      </v-list-item>
                      <v-list-item prepend-icon="mdi-chart-box-outline" class="mc-list-item">
                        <template #title><span class="text-body-2">{{ $t('predictions_home.model_cards.xai.visualization') }}</span></template>
                      </v-list-item>
                    </v-list>
                  </v-window-item>

                </v-window>

                <!-- ── Changelog ── -->
                <v-divider class="my-6"/>
                <div class="mc-section-title mb-3">
                  <v-icon size="17" class="mr-1">mdi-history</v-icon>
                  {{ $t('predictions_home.model_cards.changelog_title') }}
                </div>
                <v-alert type="success" variant="tonal" class="text-body-2">
                  {{ cardData.changelog }}
                </v-alert>

              </template>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

    </v-sheet>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { API_BASE } from '@/lib/api'
import { useTranslation } from 'i18next-vue'

const { i18next } = useTranslation()

interface HyperParams { [key: string]: string | number }
interface TrainingInfo {
  dataset_size: number
  features_count: number
  training_date: string
  hyperparameters: HyperParams
  validation_strategy: string
}
interface ModelCardData {
  name: string
  version: string
  model_type: string
  deployment_date: string
  status: string
  training: TrainingInfo
  metrics: { test_set: { accuracy: number; f1_score: number } }
  intended_use: string[]
  not_intended_for: string[]
  limitations: string[]
  recommendations: string[]
  ethical_considerations: { fairness: string; privacy: string; transparency: string }
  changelog: string
  feature_groups?: Record<string, string[]>
  features_total?: number
}

const loading = ref(true)
const error = ref('')
const cardData = ref<ModelCardData | null>(null)
const activeTab = ref('use')

// Authoritative hyperparameter values with DE/EN localized display values
const overrideEn: Record<string, string | number> = {
  n_estimators: 100,
  max_depth: 'unlimited',
  max_features: 'log2',
  min_samples_split: 10,
  min_samples_leaf: 2,
  class_weight: 'balanced',
  random_state: 42,
}
const overrideDe: Record<string, string | number> = {
  n_estimators: 100,
  max_depth: 'unbegrenzt',
  max_features: 'log2',
  min_samples_split: 10,
  min_samples_leaf: 2,
  class_weight: 'balanced',
  random_state: 42,
}

const locale = computed(() => (i18next.language?.startsWith('en') ? 'en' : 'de'))

const hyperparamsToShow = computed(() => {
  const raw: HyperParams = cardData.value?.training?.hyperparameters || {}
  const override = locale.value === 'en' ? overrideEn : overrideDe
  const keys = Array.from(new Set([...Object.keys(override), ...Object.keys(raw)]))
  return keys.map((k) => ({
    key: k,
    label: i18next.t(`predictions_home.model_cards.hyperparameters.labels.${k}`, k),
    desc: i18next.t(`predictions_home.model_cards.hyperparameters.descs.${k}`, ''),
    value: override[k] ?? raw[k],
  }))
})

const hyperparamsSummary = computed(() => {
  const override = locale.value === 'en' ? overrideEn : overrideDe
  const order = ['n_estimators', 'max_depth', 'max_features', 'min_samples_split', 'min_samples_leaf']
  const parts = order.map((k) => `${k}=${override[k] ?? (cardData.value?.training?.hyperparameters?.[k] ?? '?')}`)
  return parts.join(' \u00B7 ')
})

async function loadModelCard(showSpinner = true) {
  if (showSpinner) loading.value = true
  error.value = ''
  try {
    const lang = i18next.language?.startsWith('en') ? 'en' : 'de'
    const res = await fetch(`${API_BASE}/api/v1/model-card/json?lang=${lang}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    cardData.value = await res.json()
  } catch (err) {
    error.value = String(err)
  } finally {
    loading.value = false
  }
}

watch(() => i18next.language, () => loadModelCard(false))
onMounted(() => loadModelCard())
</script>

<style scoped>

/* ── Model Card: outer wrapper ── */
.mc-pro {
  border-radius: 10px !important;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

/* ── Gradient header ── */
.mc-header {
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    color-mix(in srgb, rgb(var(--v-theme-primary)) 80%, black) 100%);
}

/* ── Quick stats bar ── */
.mc-stats { border-bottom: 1px solid #e0e0e0; }

.stat-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 4px 8px;
}
.stat-val {
  font-size: 1.15rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.82);
  line-height: 1.2;
}
.stat-val--sm { font-size: 0.82rem; }
.stat-lbl {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(0, 0, 0, 0.48);
}

/* ── Section heading ── */
.mc-section-title {
  display: flex;
  align-items: center;
  font-size: 0.88rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: rgb(var(--v-theme-primary));
  padding-bottom: 4px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.18);
}

/* ── Sub-section heading ── */
.mc-subsection-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.mc-subsection-title--warn { color: rgb(var(--v-theme-warning)) !important; }

/* ── Metric cards ── */
.metric-card {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 8px;
  padding: 12px 16px;
}
.metric-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(0, 0, 0, 0.5);
}
.metric-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: rgb(var(--v-theme-primary));
  line-height: 1;
}

/* ── List styles ── */
.mc-list { background: transparent !important; }
.mc-list--ok :deep(.v-list-item__prepend .v-icon) { color: rgb(var(--v-theme-success)) !important; }
.mc-list--warn :deep(.v-list-item__prepend .v-icon) { color: rgb(var(--v-theme-warning)) !important; }
.mc-list-item :deep(.v-list-item-title) { white-space: normal; font-size: 0.875rem; line-height: 1.5; }
.mc-ethics-item :deep(.v-list-item-subtitle) { white-space: normal; opacity: 1; }

/* ── Hyperparameter cards ── */
.hp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}
.hp-card {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 8px;
  padding: 10px 14px;
}
.hp-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.72);
  line-height: 1.3;
}
.hp-desc {
  font-size: 0.71rem;
  line-height: 1.4;
  color: rgba(0, 0, 0, 0.48);
  margin-top: 4px;
}

/* ── Feature group chips ── */
.feature-group-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.65);
  letter-spacing: 0.03em;
}
.feature-chip {
  font-size: 0.75rem !important;
}

</style>

