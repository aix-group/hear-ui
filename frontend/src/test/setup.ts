/**
 * Vitest global setup file.
 *
 * - Installs Vuetify component stubs
 * - Initializes i18next with minimal resources for test isolation
 * - Mocks browser APIs not available in jsdom (e.g. ResizeObserver)
 */
import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import i18next from 'i18next'
import I18NextVue from 'i18next-vue'

// ── Vuetify ──────────────────────────────────────────────────────────
const vuetify = createVuetify({ components, directives })

config.global.plugins.push(vuetify)

// ── i18next ──────────────────────────────────────────────────────────
// Minimal init so $t() works in Vue components during tests.
// Real locale files are intentionally not loaded – tests should not
// depend on exact translations.
i18next.init({
  lng: 'de',
  fallbackLng: 'de',
  resources: {
    de: {
      translation: {
        'homepage.title': 'HEAR-UI',
        'homepage.subtitle': 'Cochlea-Implantat Entscheidungshilfe',
        'homepage.description': 'Beschreibung',
        'homepage.search_patients_title': 'Patienten suchen',
        'homepage.search_patients_subtitle': 'Patienten durchsuchen',
        'homepage.search_patients_text': 'Suchen Sie nach Patienten',
        'homepage.search_patients_image_alt': 'Suche',
        'homepage.create_patient_title': 'Patient erstellen',
        'homepage.create_patient_subtitle': 'Neuen Patienten anlegen',
        'homepage.create_patient_text': 'Neuen Patienten erstellen',
        'homepage.create_patient_image_alt': 'Erstellen',
        'homepage.prediction_title': 'Vorhersagen',
        'homepage.prediction_subtitle': 'KI-Vorhersagen',
        'homepage.prediction_text': 'Vorhersagen ansehen',
        'homepage.prediction_image_alt': 'Vorhersagen',
        'navbar.homepage': 'Startseite',
        'navbar.search_patients': 'Patienten suchen',
        'navbar.create_patient': 'Patient erstellen',
        'navbar.predictions': 'Vorhersagen',
        'not_found.message': 'Seite nicht gefunden',
        'not_found.home': 'Zur Startseite',
        'search.text': 'Patienten suchen...',
        'search.add_new_patient': 'Neuer Patient',
        'prediction.title': 'Vorhersage für',
        'prediction.result.title': 'Ergebnis',
        'prediction.result.probability': 'Wahrscheinlichkeit',
        'prediction.result.status.recommended': 'Empfohlen',
        'prediction.result.status.not_recommended': 'Nicht empfohlen',
        'prediction.result.description.recommended': 'CI wird empfohlen',
        'prediction.result.description.not_recommended': 'CI wird nicht empfohlen',
        'prediction.result.graph.title': 'Wahrscheinlichkeit',
        'prediction.feedback.question': 'Stimmen Sie zu?',
        'prediction.feedback.agree': 'Zustimmen',
        'prediction.feedback.disagree': 'Ablehnen',
        'prediction.feedback.comment_label': 'Kommentar',
        'prediction.feedback.comment_placeholder': 'Optional...',
        'prediction.feedback.hint': 'Optional',
        'prediction.feedback.submit': 'Absenden',
        'prediction.feedback.sending': 'Wird gesendet...',
        'prediction.feedback.required_error': 'Bitte wählen Sie eine Option',
      },
    },
    en: {
      translation: {
        'homepage.title': 'HEAR-UI',
        'not_found.message': 'Page not found',
        'not_found.home': 'Go Home',
      },
    },
  },
})

config.global.plugins.push({
  install(app) {
    app.use(I18NextVue, { i18next })
  },
})

// ── Browser API mocks ────────────────────────────────────────────────
// jsdom does not implement ResizeObserver which Vuetify needs
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver
}

// Stub CSS.supports if absent
if (typeof globalThis.CSS === 'undefined') {
  (globalThis as any).CSS = { supports: () => false }
}

// Stub URL.createObjectURL / revokeObjectURL (Plotly needs these)
if (typeof URL.createObjectURL === 'undefined') {
  URL.createObjectURL = () => 'blob:mock'
}
if (typeof URL.revokeObjectURL === 'undefined') {
  URL.revokeObjectURL = () => {}
}

// Silence console.warn from Vuetify in test output
vi.spyOn(console, 'warn').mockImplementation(() => {})

// Stub visualViewport (required by Vuetify v-overlay/v-dialog in jsdom)
if (typeof globalThis.visualViewport === 'undefined') {
  ;(globalThis as any).visualViewport = {
    width: 1024,
    height: 768,
    offsetLeft: 0,
    offsetTop: 0,
    pageLeft: 0,
    pageTop: 0,
    scale: 1,
    addEventListener: () => {},
    removeEventListener: () => {},
  }
}
