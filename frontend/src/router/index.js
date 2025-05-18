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
      component: () => import('../views/ReportView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/user',
      name: 'user',
      component: () => import('../views/UserView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  // 读取全局模式配置（测试/上线）
  const mode = import.meta.env.VITE_APP_MODE || 'production' // 通过环境变量读取模式
  if (mode === 'test') {
    // 测试模式下，所有页面均可访问，无需登录
    next()
  } else {
    // 上线模式，按原有权限控制
    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
      next({ name: 'login' })
    } else {
      next()
    }
  }
})

export default router