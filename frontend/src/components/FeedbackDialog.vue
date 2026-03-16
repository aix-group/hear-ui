<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title>Feedback</v-card-title>
      <v-card-text>
        <slot />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="dialog = false">Schließen</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export interface FeedbackData {
  modelPrediction: number
  userAssessment: number
  comments: string
  timestamp: Date
  patientId: string
  clinicianId: string
}

export default defineComponent({
  name: 'FeedbackDialog',
  setup() {
    const dialog = ref(false)

    function open() {
      dialog.value = true
    }

    function close() {
      dialog.value = false
    }

    return { dialog, open, close }
  },
})
</script>
