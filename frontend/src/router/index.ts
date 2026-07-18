import { createRouter, createWebHistory } from 'vue-router'
import StartView from '@/views/StartView.vue'
import DashboardView from '@/views/DashboardView.vue'
import PalDetailView from '@/views/PalDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: StartView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/pals/:id', name: 'pal-detail', component: PalDetailView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
