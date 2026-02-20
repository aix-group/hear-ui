<template>
  <AppLayout />
</template>

<script setup lang="ts">
import i18next from 'i18next'
import AppLayout from '@/layouts/AppLayout.vue'
import {provideFeatureDefinitions} from '@/lib/featureDefinitions'
import {featureDefinitionsStore} from '@/lib/featureDefinitionsStore'

provideFeatureDefinitions()

const loadFeatureData = async (locale?: string) => {
  await featureDefinitionsStore.loadDefinitions()
  await featureDefinitionsStore.loadLabels(locale)
}

void loadFeatureData(i18next.language)

i18next.on('languageChanged', (lng) => {
  void featureDefinitionsStore.loadLabels(lng)
})
</script>
