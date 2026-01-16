import { createRouter, createWebHistory } from 'vue-router';
import ScreenLayout from '../layouts/ScreenLayout.vue';
import MobileLayout from '../layouts/MobileLayout.vue';
import ScreenHome from '../views/ScreenHome.vue';
import MobileLogin from '../views/MobileLogin.vue';

const routes = [
  {
    path: '/',
    component: ScreenLayout,
    children: [
      { path: '', component: ScreenHome }
    ]
  },
  {
    path: '/mobile',
    component: MobileLayout,
    children: [
      { path: '', component: MobileLogin },
      { path: 'lobby', component: () => import('../views/MobileLobby.vue') },
      { path: 'host', component: () => import('../views/MobileHost.vue') }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
