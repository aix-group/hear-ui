<template>
  <AppLayout />
</template>

<script setup lang="ts">
import {onBeforeUnmount} from 'vue'
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

const onLanguageChanged = (lng: string) => {
  void featureDefinitionsStore.loadLabels(lng)
}
i18next.on('languageChanged', onLanguageChanged)

onBeforeUnmount(() => {
  i18next.off('languageChanged', onLanguageChanged)
})
</script>
