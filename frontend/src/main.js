import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import dataV from '@jiaminghi/data-view';

const app = createApp(App);
app.use(dataV);
app.use(router);
app.use(store);
app.mount('#app');
