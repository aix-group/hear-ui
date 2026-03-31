<template>
  <v-sheet class="graph-sheet" rounded="lg">
    <h4 class="graph-title">
      {{ $t('prediction.result.graph.title') }}
    </h4>

    <v-sheet class="graph-canvas" rounded="lg" elevation="0">
      <div
        class="graph-placeholder graph-placeholder-relative"
        :style="{ '--patient-x-position': patientX + '%' }"
        role="img"
        :aria-label="$t('prediction.result.graph.title') + ': ' + patientPercent + '%'"
      >
        <svg class="graph-svg" viewBox="0 33.33 100 66.67" aria-hidden="true">
          <title>{{ $t('prediction.result.graph.title') }}</title>
          <desc>{{ $t('prediction.result.graph.description', { threshold: thresholdPercent ?? 0 }) }}</desc>
          <path class="graph-curve" :d="graphPath" />
          <line class="graph-patient-line" :x1="patientX" y1="0" :x2="patientX" y2="100" />
          <circle class="graph-patient-dot" :cx="patientX" :cy="patientY" r="1.5" />
        </svg>

        <div class="graph-patient-label" :class="recommended ? 'label-left' : 'label-right'">
          {{ $t('prediction.result.graph.patient') }} {{ patientPercent }}%
        </div>
      </div>

      <div class="graph-x-axis"></div>
      <div class="graph-scale">
        <span>0</span>
        <span>100</span>
      </div>
    </v-sheet>

    <p class="graph-caption">
      {{ $t('prediction.result.graph.description', { threshold: thresholdPercent ?? 0 }) }}
    </p>
  </v-sheet>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props = defineProps<{
  predictionResult: number
  recommended: boolean
  threshold: number | null
}>()

const GRAPH_SCALE_FACTOR = 200
const MAX_Y_COORD = 96

const thresholdPercent = computed(() => {
  if (props.threshold === null) return null
  return Math.round(props.threshold * 100)
})

const patientPercent = computed(() => Math.round(props.predictionResult * 100))
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
</script>

<style scoped>
.graph-sheet {
  border: 1px solid #000;
  border-radius: 12px;
  padding: 16px;
  width: 100%;
  max-width: 360px;
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
}
.graph-title { font-weight: 600; margin: 0 0 12px 0; }
.graph-canvas { flex: 1; margin-bottom: 12px; }
.graph-caption { line-height: 1.4; margin: 0; }
.graph-placeholder { flex: 1; width: 100%; margin-bottom: 12px; }
.graph-x-axis { width: 100%; height: 1px; background-color: #d0d0d0; margin-bottom: 4px; }
.graph-scale { display: flex; justify-content: space-between; width: 100%; font-size: 12px; color: #666; padding: 0 2px; margin-bottom: 4px; }
.graph-svg { width: 100%; height: 100%; }
.graph-curve { fill: none; stroke: #000; stroke-width: 0.7; }
.graph-patient-line { stroke: #bdbdbd; stroke-width: 0.4; stroke-dasharray: 1.5 1.5; }
.graph-patient-dot { fill: rgb(var(--v-theme-primary)); }
.graph-patient-label { position: absolute; top: 2px; color: #000; }
.label-left { left: var(--patient-x-position); transform: translateX(-110%); }
.label-right { left: var(--patient-x-position); transform: translateX(10%); }
.graph-placeholder-relative { position: relative; }
</style>
