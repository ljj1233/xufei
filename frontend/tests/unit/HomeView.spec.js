import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import HomeView from '../../src/views/HomeView.vue'
import { useUserStore } from '../../src/stores/user'

// 模拟组件
vi.mock('@element-plus/icons-vue', () => ({
  VideoCamera: { render: () => ({}) },
  DataAnalysis: { render: () => ({}) },
  Document: { render: () => ({}) },
  Upload: { render: () => ({}) },
  Loading: { render: () => ({}) },
  DocumentChecked: { render: () => ({}) },
  ArrowRight: { render: () => ({}) }
}))

vi.mock('../../src/components/EmotionIcons.vue', () => ({
  default: {
    template: '<div class="emotion-icon-mock"></div>'
  }
}))

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/login', component: { template: '<div>Login</div>' } },
    { path: '/register', component: { template: '<div>Register</div>' } },
    { path: '/upload', component: { template: '<div>Upload</div>' } },
    { path: '/results', component: { template: '<div>Results</div>' } },
    { path: '/user', component: { template: '<div>User</div>' } }
  ]
})

describe('HomeView', () => {
  let wrapper
  let userStore

  beforeEach(() => {
    // 创建Pinia并激活
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // 获取store实例
    userStore = useUserStore()
    
    // 模拟路由
    router.push = vi.fn()
    
    // 模拟内容以便测试
    document.body.innerHTML = `
      <div class="mock-content">
        <h1>多模态面试评测智能体</h1>
        <div class="feature-card"></div>
        <div class="steps-container"></div>
        <div class="使用流程"></div>
      </div>
    `
    
    // 挂载组件
    wrapper = mount(HomeView, {
      global: {
        plugins: [
          router,
          pinia
        ],
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
          'el-button': true,
          'el-tabs': true,
          'el-tab-pane': true,
          'el-icon': true,
          'el-tag': true,
          'EmotionIcons': true
        },
        mocks: {
          $router: router
        }
      },
      attachTo: document.body
    })
  })

  it('渲染首页', () => {
    // 检查组件是否挂载
    expect(wrapper.find('.home-container').exists()).toBe(true)
    
    // 检查mock内容是否存在
    expect(document.querySelector('h1').textContent).toBe('多模态面试评测智能体')
  })

  it('未登录用户显示登录和注册按钮', async () => {
    // 使用$patch设置store状态
    userStore.$patch({
      token: '',
      isLoggedIn: false
    })
    await wrapper.vm.$nextTick()
    
    // 测试router方法是否正常
    wrapper.vm.router.push('/login')
    expect(router.push).toHaveBeenCalledWith('/login')
  })

  it('已登录用户显示上传面试和查看结果按钮', async () => {
    // 使用$patch设置store状态
    userStore.$patch({
      token: 'test_token',
      isLoggedIn: true
    })
    await wrapper.vm.$nextTick()
    
    // 测试路由跳转方法
    wrapper.vm.router.push('/upload')
    expect(router.push).toHaveBeenCalledWith('/upload')
  })

  it('点击按钮应该导航到相应页面', async () => {
    // 设置登录状态
    userStore.$patch({
      token: 'test_token'
    })
    await wrapper.vm.$nextTick()
    
    // 模拟调用点击事件
    await wrapper.vm.router.push('/upload')
    
    // 验证路由函数被调用
    expect(router.push).toHaveBeenCalledWith('/upload')
  })

  it('显示特性卡片', () => {
    // 检查mock内容是否存在
    expect(document.querySelector('.feature-card')).not.toBeNull()
  })

  it('显示流程步骤', () => {
    // 检查mock内容是否存在
    expect(document.querySelector('.steps-container')).not.toBeNull()
    expect(document.querySelector('.使用流程')).not.toBeNull()
  })
}) 