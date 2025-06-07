import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/register',
      name: 'register',
      // 直接重定向到登录页并自动切换到注册模式
      beforeEnter: (to, from, next) => {
        next({ name: 'login', query: { mode: 'register' } })
      }
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/UploadView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('../views/ResultsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/report/:id',
      name: 'report',
      redirect: to => {
        // 重定向到interview-report路由
        return { path: `/interview-report/${to.params.id}` }
      }
    },
    {
      path: '/user',
      name: 'user',
      component: () => import('../views/UserView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/interview-practice',
      name: 'interview-practice',
      component: () => import('../views/InterviewPracticeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/interview-session/:id',
      name: 'interview-session',
      component: () => import('../views/InterviewSessionView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/interview-report/:sessionId',
      name: 'interview-report',
      component: () => import('../views/InterviewReportView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice-history',
      name: 'practice-history',
      component: () => import('../views/PracticeHistoryView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice/:positionId',
      name: 'practice-view',
      component: () => import('../views/PracticeView.vue'),
      meta: { requiresAuth: true }
    },
    // 添加管理员路由
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 根据权限控制路由访问
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'login' })
  } else if (to.meta.requiresAdmin && !userStore.isAdmin) {
    // 管理员权限检查
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router