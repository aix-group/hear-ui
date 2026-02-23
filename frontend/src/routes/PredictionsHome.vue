<template>
  <v-container class="py-8">
    <v-sheet
        :elevation="12"
        border
        class="predictions-home-sheet"
        rounded="lg"
    >
      <!-- Title -->
      <v-row justify="start" no-gutters>
        <h1>{{ $t('predictions_home.title') }}</h1>
      </v-row>

      <v-divider class="my-6"/>



      <!-- Action Buttons -->
      <div class="d-flex justify-center ga-4 mt-8">
        <v-btn
            :to="{ name: 'SearchPatients' }"
            color="grey-lighten-4"
            class="text-black"
            prepend-icon="mdi-magnify"
            size="small"
            variant="tonal"
        >
          {{ $t('predictions_home.action_cards.search_patients.title') }}
        </v-btn>
        <v-btn
            :to="{ name: 'CreatePatient' }"
            color="grey-lighten-4"
            class="text-black"
            prepend-icon="mdi-account-plus"
            size="small"
            variant="tonal"
        >
          {{ $t('predictions_home.action_cards.create_patient.title') }}
        </v-btn>
      </div>

      <v-divider class="my-6 mb-8"/>

      <!-- Model Card Section -->
      <v-row>
        <v-col>
          <v-card class="model-card-professional" elevation="3">

            <!-- Header -->
            <v-card-title class="model-card-header text-white pa-6">
              <div class="text-h4 font-weight-bold">{{ meta.name }}</div>
            </v-card-title>

            <!-- Metadata Bar -->
            <div class="model-card-metadata pa-4 bg-grey-lighten-4">
              <v-row dense>
                <v-col cols="12" md="4">
                  <div class="text-caption text-grey-darken-1">{{ $t('predictions_home.model_cards.header.version') }}</div>
                  <div class="text-body-1 font-weight-medium">{{ meta.version }}</div>
                </v-col>
                <v-col cols="12" md="4">
                  <div class="text-caption text-grey-darken-1">{{ $t('predictions_home.model_cards.header.model_type') }}</div>
                  <div class="text-body-1 font-weight-medium">{{ meta.modelType }}</div>
                </v-col>
                <v-col cols="12" md="4">
                  <div class="text-caption text-grey-darken-1">{{ $t('predictions_home.model_cards.header.last_updated') }}</div>
                  <div class="text-body-1 font-weight-medium">{{ meta.lastUpdated }}</div>
                </v-col>
              </v-row>
            </div>

            <v-card-text class="pa-6">
              <!-- Loading State -->
              <div v-if="loading" class="text-center py-12">
                <v-progress-circular indeterminate color="primary" size="64"/>
                <p class="mt-4 text-grey">{{ $t('predictions_home.model_cards.loading', { defaultValue: 'Lädt...' }) }}</p>
              </div>

              <!-- Error State -->
              <div v-else-if="error" class="text-center py-12">
                <v-icon color="error" size="64">mdi-alert-circle-outline</v-icon>
                <p class="mt-4 text-error">{{ error }}</p>
                <v-btn @click="loadModelCard" variant="outlined" color="primary" class="mt-4">
                  {{ $t('predictions_home.model_cards.retry', { defaultValue: 'Erneut versuchen' }) }}
                </v-btn>
              </div>

              <!-- Rendered Markdown -->
              <div
                v-else
                class="model-card-markdown"
                v-html="renderedHtml"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

    </v-sheet>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { API_BASE } from '@/lib/api'
import { useTranslation } from 'i18next-vue'

const { i18next } = useTranslation()

const loading = ref(true)
const error = ref('')
const rawMarkdown = ref('')

interface Meta { name: string; version: string; modelType: string; lastUpdated: string }

const meta = ref<Meta>({
  name: 'HEAR CI Prediction Model',
  version: 'v3.0',
  modelType: 'RandomForestClassifier',
  lastUpdated: new Date().toISOString().slice(0, 10),
})

// Configure marked: GitHub-flavoured Markdown with line breaks
marked.setOptions({ gfm: true, breaks: true } as Parameters<typeof marked.setOptions>[0])

const renderedHtml = computed(() => {
  if (!rawMarkdown.value) return ''
  const html = marked.parse(rawMarkdown.value) as string
  return DOMPurify.sanitize(html)
})

/**
 * Strip the h1 title and Version/ModelType/LastUpdated metadata lines
 * from the raw markdown before rendering, since they are already shown
 * in the header bar above the rendered content.
 */
function stripHeaderBlock(md: string): string {
  return md
    // Remove the h1 line (e.g. "# HEAR CI Prediction Model")
    .replace(/^#\s+.+\n?/m, '')
    // Remove the three metadata lines inserted by the backend template
    .replace(/\*\*(?:Version|Model Type|Modelltyp|Letzte Aktualisierung|Last Updated):\*\*.*\n?/gi, '')
    // Collapse multiple consecutive blank lines left by the removal
    .replace(/\n{3,}/g, '\n\n')
    .trimStart()
}

/** Extract the handful of metadata values we show in the header bar. */
function extractMeta(md: string): Meta {
  const title = md.match(/^#\s+(.+)$/m)?.[1] ?? meta.value.name
  const version = md.match(/\*\*Version:\*\*\s*([^\s\n]+)/i)?.[1] ?? meta.value.version
  const modelType = md.match(/\*\*(?:Modelltyp|Model Type):\*\*\s*(.+?)(?:\s{2,}|\n)/i)?.[1]?.trim() ?? meta.value.modelType
  const lastUpdated = md.match(/\*\*(?:Letzte Aktualisierung|Last Updated):\*\*\s*(.+?)(?:\s{2,}|\n)/i)?.[1]?.trim() ?? meta.value.lastUpdated
  return { name: title, version, modelType, lastUpdated }
}

async function loadModelCard() {
  loading.value = true
  error.value = ''
  try {
    const lang = i18next.language?.startsWith('en') ? 'en' : 'de'
    const res = await fetch(`${API_BASE}/api/v1/model-card?lang=${lang}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const text = await res.text()
    meta.value = extractMeta(text)
    rawMarkdown.value = stripHeaderBlock(text)
  } catch (err) {
    error.value = String(err)
  } finally {
    loading.value = false
  }
}

watch(() => i18next.language, () => loadModelCard())
onMounted(() => loadModelCard())
</script>

<style scoped>
.predictions-home-sheet {
  padding: 32px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}

/* Professional Model Card Styles */
.model-card-professional {
  border-radius: 8px !important;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.model-card-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-darken-1)) 100%);
}

.model-card-metadata {
  border-bottom: 1px solid #e0e0e0;
}

/* ── Rendered Markdown Styles ─────────────────────────────────── */
.model-card-markdown {
  line-height: 1.8;
  color: rgba(0, 0, 0, 0.82);
  font-size: 0.96rem;
  font-family: inherit;
}

/* H1 (model name) – hidden, already in header bar */
.model-card-markdown :deep(h1) { display: none; }

/* ── Section headings (h2) ──────────────────────────── */
.model-card-markdown :deep(h2) {
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(90deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-primary-darken-1), 0.85) 100%);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  margin: 2.2rem 0 0.9rem;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* ── Sub-group headings (h3) ──────────────────────────── */
.model-card-markdown :deep(h3) {
  font-size: 0.9rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin: 1.4rem 0 0.5rem;
  padding-bottom: 0.2rem;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.2);
}

/* ── Paragraphs ──────────────────────────── */
.model-card-markdown :deep(p) {
  margin: 0.5rem 0;
}

/* ── Unordered lists (bullet points) ──────────────────────────── */
.model-card-markdown :deep(ul) {
  padding-left: 1.4rem;
  margin: 0.4rem 0 1rem;
}

.model-card-markdown :deep(ul li) {
  margin-bottom: 0.35rem;
  line-height: 1.7;
  position: relative;
}

.model-card-markdown :deep(ul li::marker) {
  color: rgb(var(--v-theme-primary));
}

/* ── Bold labels inside paragraphs/lists ──────────────────────────── */
.model-card-markdown :deep(li strong),
.model-card-markdown :deep(p strong) {
  color: rgba(0, 0, 0, 0.87);
}

/* ── Italic text ──────────────────────────── */
.model-card-markdown :deep(em) {
  color: rgba(0, 0, 0, 0.55);
  font-size: 0.9rem;
}

/* ── Horizontal rule – styled divider ──────────────────────────── */
.model-card-markdown :deep(hr) {
  border: none;
  border-top: 2px dashed rgba(var(--v-theme-primary), 0.2);
  margin: 2rem 0;
}

/* ── Blockquote – highlighted note ──────────────────────────── */
.model-card-markdown :deep(blockquote) {
  border-left: 4px solid rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.06);
  margin: 1.2rem 0;
  padding: 0.75rem 1.1rem;
  border-radius: 0 8px 8px 0;
  color: rgba(0, 0, 0, 0.72);
  font-style: normal;
  font-size: 0.93rem;
}

.model-card-markdown :deep(blockquote p) {
  margin: 0;
}

/* ── Inline code ──────────────────────────── */
.model-card-markdown :deep(code) {
  background: #f4f4f4;
  border-radius: 4px;
  padding: 0.1em 0.4em;
  font-size: 0.86em;
  color: #c62828;
  font-family: 'Courier New', monospace;
}

/* ── Ordered list → feature chip grid ──────────────────────────── */
.model-card-markdown :deep(ol) {
  list-style: none;
  padding-left: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.6rem 0 1.2rem;
}

.model-card-markdown :deep(ol li) {
  background: rgba(var(--v-theme-primary), 0.07);
  border: 1px solid rgba(var(--v-theme-primary), 0.28);
  border-radius: 20px;
  padding: 0.25rem 0.85rem;
  font-size: 0.81rem;
  color: rgb(var(--v-theme-primary));
  margin-bottom: 0;
  transition: background 0.15s, border-color 0.15s;
}

.model-card-markdown :deep(ol li:hover) {
  background: rgba(var(--v-theme-primary), 0.14);
  border-color: rgba(var(--v-theme-primary), 0.5);
}

/* ── Tables (metrics rows) ──────────────────────────── */
.model-card-markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8rem 0 1.2rem;
  font-size: 0.91rem;
}

.model-card-markdown :deep(th) {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  font-weight: 700;
  padding: 0.5rem 0.8rem;
  text-align: left;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.3);
}

.model-card-markdown :deep(td) {
  padding: 0.4rem 0.8rem;
  border-bottom: 1px solid #eeeeee;
  vertical-align: middle;
}

.model-card-markdown :deep(tr:last-child td) {
  border-bottom: none;
}

/* ── Responsive ──────────────────────────── */
@media (max-width: 768px) {
  .model-card-markdown { font-size: 0.92rem; }
  .model-card-markdown :deep(h2) { font-size: 0.95rem; padding: 0.4rem 0.8rem; }
  .model-card-markdown :deep(h3) { font-size: 0.85rem; }
  .model-card-markdown :deep(ol li) { white-space: normal; font-size: 0.78rem; }
}
</style>

