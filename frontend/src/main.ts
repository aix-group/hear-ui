import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import {vuetify} from './plugins/vuetify'
import 'vuetify/styles'
import './styles/main.css'
import '@mdi/font/css/materialdesignicons.css'
import installI18n from "./i18n.ts";
import {logger} from "@/lib/logger";
import {OpenAPI} from "@/client";

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
    logger.error('Unhandled error:', err, '\nComponent:', instance, '\nInfo:', info)
}

// Register a request interceptor that attaches the XSRF token cookie (if set
// by the backend) as an X-XSRF-TOKEN header on every mutating request.
OpenAPI.interceptors.request.use((config) => {
    const xsrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('XSRF-TOKEN='))
        ?.split('=')[1]
    if (xsrfToken && config.headers) {
        config.headers['X-XSRF-TOKEN'] = decodeURIComponent(xsrfToken)
    }
    return config
})

app.use(router)
app.use(vuetify)
installI18n(app)

app.mount('#app')
