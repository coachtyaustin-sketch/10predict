import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/predictions',
      name: 'predictions',
      component: () => import('../views/PredictionsView.vue'),
    },
    {
      path: '/predictions/:id',
      name: 'prediction-detail',
      component: () => import('../views/PredictionDetailView.vue'),
    },
    {
      path: '/research',
      name: 'research',
      component: () => import('../views/ResearchView.vue'),
    },
  ],
})

export default router
