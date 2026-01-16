// Expose connection for testing
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { startConnection, connection } from './services/signalr'

import './style.css'

const app = createApp(App)

app.use(router)

app.mount('#app')

// Start SignalR
startConnection();

// Expose to window for E2E testing
window.__SIGNALR_CONNECTION__ = connection;
