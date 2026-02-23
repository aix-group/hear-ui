
<template>
  <v-card>
    <v-card-title>Model Card: {{ modelCard?.name }}</v-card-title>
    <v-card-text>
      <v-list v-if="modelCard">
        <v-list-item>
          <v-list-item-title>Version</v-list-item-title>
          <v-list-item-subtitle>{{ modelCard.version }}</v-list-item-subtitle>
        </v-list-item>
        <!-- Weitere Modellinformationen -->
      </v-list>

      <v-expansion-panels>
        <!-- Metrics panel removed - metrics are not populated in current implementation -->
        <!-- To add metrics: populate ModelMetrics in backend/app/models/model_card/model_card.py -->
        <!-- and update the markdown renderer in backend/app/api/routes/model_card.py -->
        
        <!-- Weitere Panels für andere Kategorien -->
      </v-expansion-panels>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { API_BASE } from '@/lib/api'

interface ModelCardData {
  name: string
  version: string
  [key: string]: unknown
}

export default defineComponent({
  name: 'ModelCard',
  data() {
    return {
      modelCard: null as ModelCardData | null
    }
  },
  async created() {
    // Lade Model Card Daten vom Backend
    const response = await fetch(`${API_BASE}/api/v1/model-card`)
    this.modelCard = await response.json()
  }
})
</script>
