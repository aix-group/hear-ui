import {createApp} from 'vue'
import App from './App.vue'
import router from './router'
import {vuetify} from './plugins/vuetify'
import 'vuetify/styles'
import './styles/main.css'
import '@mdi/font/css/materialdesignicons.css'
import installI18n from "./i18n.ts";

const app = createApp(App)

app.use(router)
app.use(vuetify)
installI18n(app)

app.mount('#app')
