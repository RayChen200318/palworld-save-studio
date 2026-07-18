import { createRouter, createWebHistory } from 'vue-router'
import StartView from '@/views/StartView.vue'
import DashboardView from '@/views/DashboardView.vue'
import PalsView from '@/views/PalsView.vue'
import PalDetailView from '@/views/PalDetailView.vue'
import PlayersView from '@/views/PlayersView.vue'
import TechnologyView from '@/views/TechnologyView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: StartView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/pals', name: 'pals', component: PalsView },
    { path: '/pals/:id', name: 'pal-detail', component: PalDetailView },
    { path: '/players', name: 'players', component: PlayersView },
    { path: '/technology', name: 'technology', component: TechnologyView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
