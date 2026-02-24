import i18next from 'i18next'
import I18NextVue from 'i18next-vue'
import LanguageDetector from 'i18next-browser-languagedetector'
import {App} from "vue";
import de from './locales/de.json';
import en from './locales/en.json';

// am besten erstmal frontend-i18n.md lesen

i18next
    // detect user language (will read from localStorage if present)
    .use(LanguageDetector)
    // init i18next
    // for all options read: https://www.i18next.com/overview/configuration-options
    .init({
        debug: false,
        // Do NOT force a default `lng` here — allow the detector to restore
        // the user's previously selected language (cached in localStorage).
        fallbackLng: 'de',
        detection: {
            // prefer an explicit saved value in localStorage, then browser settings
            order: ['localStorage', 'navigator'],
            caches: ['localStorage']
        },
        defaultNS: 'translation',
        ns: ['translation'],
        resources: {
            de: de,
            en: en
        }
    });

export default function installI18n(app: App) {
    app.use(I18NextVue, {i18next})
    return app
}
