import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Selbst gehostete Fonts (GDPR — keine externen Requests an Google Fonts)
import '@fontsource/source-sans-3/400.css'
import '@fontsource/source-sans-3/600.css'
import '@fontsource/source-sans-3/700.css'
import '@fontsource/fira-code/400.css'
import '@fontsource/fira-code/500.css'

import './styles/tokens.css'
import App from './App.vue'
import router from './router'
import { useWjStore } from './stores/wj_store'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// Wirtschaftsjahre + Datenquellen-Status vom Backend laden (Mock-Fallback im Store).
useWjStore().laden()
