<template>
  <div>
    <h2 class="mb-2">{{ $t('prediction.explanations.title') }}</h2>
    <p class="text-body-2 text-medium-emphasis mb-4">
      {{ $t('prediction.explanations.subtitle') }}
    </p>
    <div
      ref="plotEl"
      role="img"
      :aria-label="$t('prediction.explanations.title')"
      :style="{ width: '100%', height: plotHeight + 'px' }"
    ></div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch, onMounted } from 'vue'
import * as Plotly from 'plotly.js-dist-min'

export interface MatchedFeature {
  rawKey: string
  normalizedKey: string
  description?: string
  section?: string
  featureKey: string
  importance: number
  rawValue: unknown
}

const props = defineProps<{
  matchedFeatures: MatchedFeature[]
  featureLabels: string[]
  featureImportances: number[]
  sectionBoundaries: Array<{ yStart: number; label: string; isPositive: boolean }>
  language: string
}>()

const plotEl = ref<HTMLDivElement | null>(null)

const plotHeight = computed(() => {
  const numFeatures = props.featureLabels.length
  if (numFeatures === 0) return 320
  return numFeatures * 40 + 80
})

function wrapLabel(label: string, maxChars = 32) {
  const words = label.split(/\s+/)
  const lines: string[] = []
  let line = ""
  for (const w of words) {
    const next = line ? `${line} ${w}` : w
    if (next.length > maxChars) {
      if (line) lines.push(line)
      line = w
    } else { line = next }
  }
  if (line) lines.push(line)
  return lines.join("<br>")
}

function render() {
  if (!plotEl.value) return
  if (props.featureLabels.length === 0) {
    Plotly.purge(plotEl.value)
    return
  }

  const yVals = props.featureLabels.map((_, i) => i)
  const wrapped = props.featureLabels.map((l) => wrapLabel(l, 44))
  const isEn = props.language?.startsWith('en')

  const posIdx = props.featureImportances.map((v, i) => v >= 0 ? i : -1).filter(i => i >= 0)
  const negIdx = props.featureImportances.map((v, i) => v < 0 ? i : -1).filter(i => i >= 0)

  const data: Plotly.Data[] = [
    {
      type: "bar", orientation: "h",
      name: isEn ? "Increases probability" : "Erh\u00f6ht Wahrscheinlichkeit",
      x: posIdx.map(i => props.featureImportances[i]),
      y: posIdx.map(i => yVals[i]),
      marker: { color: 'rgba(221, 5, 74, 0.78)', line: { width: 0 } },
      customdata: posIdx.map(i => props.featureLabels[i]),
      hovertemplate: isEn
        ? "<b>%{customdata}</b><br>Contribution: %{x:.4f}<extra></extra>"
        : "<b>%{customdata}</b><br>Beitrag: %{x:.4f}<extra></extra>",
      showlegend: true,
    },
    {
      type: "bar", orientation: "h",
      name: isEn ? "Decreases probability" : "Senkt Wahrscheinlichkeit",
      x: negIdx.map(i => props.featureImportances[i]),
      y: negIdx.map(i => yVals[i]),
      marker: { color: 'rgba(33, 150, 243, 0.78)', line: { width: 0 } },
      customdata: negIdx.map(i => props.featureLabels[i]),
      hovertemplate: isEn
        ? "<b>%{customdata}</b><br>Contribution: %{x:.4f}<extra></extra>"
        : "<b>%{customdata}</b><br>Beitrag: %{x:.4f}<extra></extra>",
      showlegend: true,
    },
  ]

  const annotations: Partial<Plotly.Annotations[number]>[] = wrapped.map((txt, i) => ({
    xref: "paper", yref: "y", x: 0, xanchor: "right", xshift: -10,
    y: i, text: txt, showarrow: false, align: "left", valign: "middle",
    font: { size: 11, color: '#333' },
  }))

  props.sectionBoundaries.forEach(({ yStart, label, isPositive }) => {
    annotations.push({
      xref: 'paper', yref: 'y', x: 1.02, xanchor: 'left', xshift: 0,
      y: yStart, text: `<b>${label}</b>`, showarrow: false, align: 'left', valign: 'middle',
      font: { size: 12, color: isPositive ? '#DD054A' : '#2196F3', family: 'Inter, Roboto, system-ui' },
      bgcolor: isPositive ? 'rgba(221,5,74,0.06)' : 'rgba(33,150,243,0.06)',
      bordercolor: isPositive ? '#DD054A' : '#2196F3', borderwidth: 1, borderpad: 6,
    })
  })

  const layout: Partial<Plotly.Layout> = {
    height: plotHeight.value,
    xaxis: {
      title: { text: isEn ? "Contribution to prediction" : "Beitrag zur Vorhersage", font: { size: 12, color: '#666' } },
      automargin: true, zeroline: true, zerolinewidth: 2, zerolinecolor: '#999', gridcolor: '#eee', gridwidth: 1,
    },
    yaxis: { showticklabels: false, automargin: false },
    legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'left', x: 0, font: { size: 11 } },
    annotations,
    margin: {
      l: Math.max(240, Math.min(520, Math.max(...wrapped.map((lbl) => Math.max(...lbl.split('<br>').map((s) => s.replace(/<[^>]+>/g, '').length)))) * 7)),
      r: props.sectionBoundaries.length
        ? Math.max(160, Math.min(280, Math.max(...props.sectionBoundaries.map((b) => b.label.length)) * 8 + 32))
        : 40,
      t: 10, b: 40,
    },
    bargap: 0.28,
  }

  Plotly.react(plotEl.value, data, layout, { displayModeBar: false, responsive: true })
}

watch([() => props.featureLabels, () => props.featureImportances, () => props.language], () => render())
onMounted(() => render())

defineExpose({ render })
</script>
