<template>
  <v-app id="hear-ui">
    <!-- Navigation Drawer -->
    <v-navigation-drawer
        v-model="drawer"
        class="pt-4"
        color="primary"
        width="260"
        app
    >
      <v-list
          density="comfortable"
          nav
          class="drawer-list"
      >
        <v-list-item
          :to="{ name: 'Home' }"
          class="text-white text-body-1 nav-item"
          prepend-icon="mdi-home-outline"
          :title="$t('navbar.homepage')"
          @click="drawer = false"
        />

        <v-list-item
          :to="{ name: 'SearchPatients' }"
          class="text-white text-body-1 nav-item"
          prepend-icon="mdi-magnify"
          :title="$t('navbar.search_patients')"
          @click="drawer = false"
        />

        <v-list-item
          :to="{ name: 'CreatePatient' }"
          class="text-white text-body-1 nav-item"
          prepend-icon="mdi-account-plus"
          :title="$t('navbar.create_patient')"
          @click="drawer = false"
        />

        <v-list-item
          :to="{ name: 'PredictionsHome' }"
          class="text-white text-body-1 nav-item"
          prepend-icon="mdi-trending-up"
          :title="$t('navbar.predictions')"
          @click="drawer = false"
        />
      </v-list>
    </v-navigation-drawer>


    <!-- Top App Bar -->
    <v-app-bar color="primary" app :elevation="0">
      <v-app-bar-nav-icon @click="drawer = !drawer"/>
      <v-app-bar-title class="text-white" :to="{ name: 'Home' }">
        <router-link :to="{ name: 'Home' }" class="d-flex align-center">
          <v-img
              src="/assets/vectors/logo_white.svg"
              contain
              max-height="40"
              max-width="120"
          />
        </router-link>

      </v-app-bar-title>
      <v-btn variant="outlined"
             density="comfortable"
             prepend-icon="mdi-translate"
             size="large"
             rounded="xs"
             class="language-button"
             @click="switch_language"
      >
        {{ languages[curr_language] }}
      </v-btn>
    </v-app-bar>

    <!-- Main Content (your router pages render here) -->
    <v-main class="pa-4">
      <router-view/>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import {onMounted, onBeforeUnmount, ref} from "vue"
import i18next from "i18next";

const drawer = ref(false)
const curr_language = ref(0)
const languages = ref(["de", "en"])

const syncLanguageIndex = (lng: string) => {
  const idx = languages.value.indexOf(lng)
  curr_language.value = idx >= 0 ? idx : 0
}


function switch_language() {
  curr_language.value++
  curr_language.value = curr_language.value % languages.value.length
  i18next.changeLanguage(languages.value[curr_language.value])
}

onMounted(() => {
  const resources = i18next.options?.resources
  if (resources && typeof resources === 'object') {
    languages.value = Object.keys(resources)
    syncLanguageIndex(i18next.language)
    return
  }
  languages.value = ["de", "en"]
  syncLanguageIndex(i18next.language)
})

const onLanguageChanged = (lng: string) => {
  syncLanguageIndex(lng)
}

i18next.on('languageChanged', onLanguageChanged)

onBeforeUnmount(() => {
  i18next.off('languageChanged', onLanguageChanged)
})

</script>

<style scoped>

.nav-item {
  border-radius: 0 999px 999px 0;
  margin-bottom: 8px;
}

/* remove ALL CAPS look from list text */
.nav-item :deep(.v-list-item-title) {
  text-transform: none;
  letter-spacing: 0.02em;
  font-weight: 500;
}

.nav-item :deep(.v-list-item__prepend) {
  padding-left: 20px !important; /* padding BEFORE the icon */
}

.drawer-list {
  padding-left: 0 !important;
  padding-right: 16px !important;
}

.language-button {
  margin-right: 16px !important;
}
</style>

<style>
/* Global utility classes used across the layout and its pages */

.v-sheet.details-sheet{
  padding: 32px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}
</style>
