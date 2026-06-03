import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/analysis',
    },
    {
      path: '/analysis',
      name: 'Analysis',
      component: () => import('../views/AnalysisView.vue'),
    },
    {
      path: '/analysis/:id',
      name: 'AnalysisDetail',
      component: () => import('../views/AnalysisDetail.vue'),
    },
    {
      path: '/bid',
      name: 'BidList',
      component: () => import('../views/BidListView.vue'),
    },
    {
      path: '/bid/:id',
      name: 'BidEditor',
      component: () => import('../views/BidEditorView.vue'),
    },
    {
      path: '/compliance',
      name: 'Compliance',
      component: () => import('../views/ComplianceView.vue'),
    },
    {
      path: '/compliance/:id',
      name: 'ComplianceResult',
      component: () => import('../views/ComplianceResult.vue'),
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('../views/KnowledgeView.vue'),
    },
  ],
})

export default router
