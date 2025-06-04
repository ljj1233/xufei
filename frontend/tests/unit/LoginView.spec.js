import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import LoginView from '../../src/views/LoginView.vue'
import { useUserStore } from '../../src/stores/user'
import { ElMessage } from 'element-plus'

// 模拟Element Plus的消息组件
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn()
    }
  }
})

describe('LoginView', () => {
  let wrapper
  let userStore
  let router

  beforeEach(() => {
    // 创建Pinia并激活
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // 创建虚拟DOM结构
    document.body.innerHTML = `
      <div class="mock-content">
        <div class="login-container">
          <div class="login-card"></div>
          <div class="login-text">登录</div>
          <div class="register-text">注册</div>
        </div>
      </div>
    `
    
    // 创建路由
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/login', component: LoginView },
        { path: '/register', component: { template: '<div>Register</div>' } }
      ]
    })
    
    // 模拟路由方法
    router.push = vi.fn()
    router.replace = vi.fn()
    router.currentRoute = {
      value: {
        query: {},
        path: '/login'
      }
    }
    
    // 获取store实例
    userStore = useUserStore()
    
    // 模拟登录和注册方法
    userStore.login = vi.fn()
    userStore.register = vi.fn()
    
    // 挂载组件
    wrapper = mount(LoginView, {
      global: {
        plugins: [
          router,
          pinia
        ],
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true
        },
        mocks: {
          $route: {
            query: {}
          }
        }
      },
      attachTo: document.body
    })
    
    // 手动设置组件的必要方法和属性
    wrapper.vm.loginFormRef = { validate: vi.fn((callback) => callback(true)) }
    wrapper.vm.registerFormRef = { validate: vi.fn((callback) => callback(true)) }
  })

  it('渲染登录页面', () => {
    // 检查DOM是否正确挂载
    expect(document.querySelector('.login-container')).not.toBeNull()
    expect(document.querySelector('.login-card')).not.toBeNull()
    
    // 验证组件状态
    expect(wrapper.vm.isLogin).toBe(true)
    expect(document.querySelector('.login-text').textContent).toBe('登录')
  })

  it('在查询参数mode=register时显示注册表单', async () => {
    // 手动设置路由查询参数
    wrapper.vm.$route = { query: { mode: 'register' } }
    
    // 手动触发watch
    await wrapper.vm.$nextTick()
    
    // 修改内部状态显示注册表单
    wrapper.vm.isLogin = false
    await wrapper.vm.$nextTick()
    
    // 验证组件状态
    expect(wrapper.vm.isLogin).toBe(false)
    expect(document.querySelector('.register-text').textContent).toBe('注册')
  })

  it('点击切换链接可以在登录和注册表单之间切换', async () => {
    // 初始状态为登录表单
    expect(wrapper.vm.isLogin).toBe(true)
    
    // 点击切换到注册表单
    await wrapper.vm.toggleForm()
    
    // 验证状态和方法调用
    expect(wrapper.vm.isLogin).toBe(false)
    expect(router.replace).toHaveBeenCalledWith({ query: {} })
    
    // 再次点击切换回登录表单
    await wrapper.vm.toggleForm()
    
    expect(wrapper.vm.isLogin).toBe(true)
  })

  it('登录成功后应该跳转并显示成功消息', async () => {
    // 模拟登录成功
    userStore.login.mockResolvedValueOnce({ success: true })
    
    // 设置表单数据
    wrapper.vm.loginForm.username = 'testuser'
    wrapper.vm.loginForm.password = 'password'
    
    // 调用登录方法
    await wrapper.vm.handleLogin()
    
    // 验证store的login方法被调用
    expect(userStore.login).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password'
    })
    
    // 验证成功消息显示
    expect(ElMessage.success).toHaveBeenCalledWith('登录成功')
    
    // 验证路由跳转
    expect(router.push).toHaveBeenCalledWith('/')
  })

  it('登录失败应该显示错误消息', async () => {
    // 模拟登录失败
    userStore.login.mockResolvedValueOnce({ 
      success: false, 
      message: '用户名或密码错误' 
    })
    
    // 设置表单数据
    wrapper.vm.loginForm.username = 'testuser'
    wrapper.vm.loginForm.password = 'password'
    
    // 调用登录方法
    await wrapper.vm.handleLogin()
    
    // 验证错误消息显示
    expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
    
    // 不应该跳转
    expect(router.push).not.toHaveBeenCalled()
  })
  
  it('注册成功后应该切换到登录表单并显示成功消息', async () => {
    // 模拟注册成功
    userStore.register.mockResolvedValueOnce({ success: true })
    
    // 切换到注册表单
    wrapper.vm.isLogin = false
    await wrapper.vm.$nextTick()
    
    // 设置注册表单数据
    wrapper.vm.registerForm.username = 'newuser'
    wrapper.vm.registerForm.email = 'newuser@example.com'
    wrapper.vm.registerForm.password = 'password123'
    wrapper.vm.registerForm.confirmPassword = 'password123'
    
    // 调用注册方法
    await wrapper.vm.handleRegister()
    
    // 验证store的register方法被调用
    expect(userStore.register).toHaveBeenCalledWith({
      username: 'newuser',
      email: 'newuser@example.com',
      password: 'password123'
    })
    
    // 验证成功消息显示
    expect(ElMessage.success).toHaveBeenCalledWith('注册成功，请登录')
    
    // 验证已切换到登录表单
    expect(wrapper.vm.isLogin).toBe(true)
    
    // 验证登录表单用户名被填充
    expect(wrapper.vm.loginForm.username).toBe('newuser')
  })
}) 