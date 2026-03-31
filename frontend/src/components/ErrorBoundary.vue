<template>
  <slot v-if="!hasError" />
  <v-alert v-else type="error" variant="tonal" class="ma-4">
    <v-alert-title>{{ title }}</v-alert-title>
    <p class="mt-2">{{ message }}</p>
    <v-btn class="mt-3" variant="outlined" size="small" @click="reset">
      {{ retryLabel }}
    </v-btn>
  </v-alert>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from "vue"
import { logger } from "@/lib/logger"

withDefaults(
  defineProps<{
    title?: string
    message?: string
    retryLabel?: string
  }>(),
  {
    title: "Etwas ist schiefgelaufen",
    message:
      "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
    retryLabel: "Erneut versuchen",
  },
)

const hasError = ref(false)

onErrorCaptured((err) => {
  logger.error("ErrorBoundary caught:", err)
  hasError.value = true
  return false
})

function reset() {
  hasError.value = false
}
</script>
