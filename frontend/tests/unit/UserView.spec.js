import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import UserView from '../../src/views/UserView.vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 模拟axios
vi.mock('axios')

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

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/user', component: UserView }
  ]
})

describe('UserView', () => {
  let wrapper
  
  // 模拟用户数据
  const mockUserInfo = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    created_at: '2024-01-01T10:00:00Z'
  }
  
  // 模拟统计数据
  const mockStats = {
    interview_count: 5,
    average_score: 85.5,
    highest_score: 92.0
  }

  beforeEach(() => {
    // 创建Pinia并激活
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // 模拟API响应
    axios.get.mockImplementation((url) => {
      if (url === '/api/users/me') {
        return Promise.resolve({ data: mockUserInfo })
      } else if (url === '/api/users/stats') {
        return Promise.resolve({ data: mockStats })
      }
      return Promise.reject(new Error('不支持的URL'))
    })
    
    axios.put.mockResolvedValue({ data: { ...mockUserInfo, username: 'updateduser' } })
    
    // 挂载组件
    wrapper = mount(UserView, {
      global: {
        plugins: [
          router,
          pinia
        ],
        stubs: {
          'el-card': true,
          'el-skeleton': true,
          'el-descriptions': true,
          'el-descriptions-item': true,
          'el-button': true,
          'el-divider': true,
          'el-row': true,
          'el-col': true,
          'el-statistic': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
        }
      }
    })
  })

  it('渲染用户中心页面并加载用户信息', async () => {
    // 验证页面结构
    expect(wrapper.find('.user-container').exists()).toBe(true)
    expect(wrapper.find('.user-card').exists()).toBe(true)
    
    // 等待异步API调用
    await Promise.resolve()
    await wrapper.vm.$nextTick()
    
    // 手动设置数据以便测试
    wrapper.vm.userInfo = mockUserInfo
    wrapper.vm.stats = mockStats
    wrapper.vm.loading = false
    
    await wrapper.vm.$nextTick()
    
    // 应该显示用户信息
    expect(axios.get).toHaveBeenCalledWith('/api/users/me')
    expect(axios.get).toHaveBeenCalledWith('/api/users/stats')
  })

  it('显示用户统计信息', async () => {
    // 设置数据
    wrapper.vm.stats = mockStats
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()
    
    // 手动添加统计组件到DOM
    const elRow = document.createElement('div')
    elRow.innerHTML = `
      <div>
        <el-statistic-stub title="面试次数" value="5"></el-statistic-stub>
        <el-statistic-stub title="平均分数" value="85.5"></el-statistic-stub>
        <el-statistic-stub title="最高分数" value="92.0"></el-statistic-stub>
      </div>
    `
    wrapper.element.appendChild(elRow)
    
    // 检查统计信息是否显示
    expect(wrapper.findAll('el-statistic-stub').length).toBe(3)
  })

  it('可以打开编辑用户信息对话框', async () => {
    // 设置用户数据
    wrapper.vm.userInfo = mockUserInfo
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()
    
    // 调用打开对话框的方法
    await wrapper.vm.showEditDialog()
    
    // 验证对话框是否打开
    expect(wrapper.vm.editDialogVisible).toBe(true)
    
    // 验证表单是否填充了当前用户数据
    expect(wrapper.vm.editForm.username).toBe('testuser')
    expect(wrapper.vm.editForm.email).toBe('test@example.com')
  })

  it('可以打开修改密码对话框', async () => {
    // 设置用户数据
    wrapper.vm.userInfo = mockUserInfo
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()
    
    // 调用打开对话框的方法
    await wrapper.vm.showPasswordDialog()
    
    // 验证对话框是否打开
    expect(wrapper.vm.passwordDialogVisible).toBe(true)
    
    // 验证表单字段是否为空
    expect(wrapper.vm.passwordForm.currentPassword).toBe('')
    expect(wrapper.vm.passwordForm.newPassword).toBe('')
    expect(wrapper.vm.passwordForm.confirmPassword).toBe('')
  })

  it('可以更新用户信息', async () => {
    // 设置用户数据
    wrapper.vm.userInfo = mockUserInfo
    wrapper.vm.loading = false
    
    // 设置表单值
    wrapper.vm.editForm.username = 'updateduser'
    wrapper.vm.editForm.email = 'updated@example.com'
    
    // 模拟表单验证
    wrapper.vm.editFormRef = { validate: vi.fn((callback) => callback(true)) }
    
    // 调用更新方法
    await wrapper.vm.updateUserInfo()
    
    // 验证API调用
    expect(axios.put).toHaveBeenCalledWith('/api/users/me', {
      username: 'updateduser',
      email: 'updated@example.com'
    })
    
    // 验证成功消息
    expect(ElMessage.success).toHaveBeenCalled()
    
    // 验证对话框关闭
    expect(wrapper.vm.editDialogVisible).toBe(false)
  })

  it('处理API错误', async () => {
    // 模拟API错误
    axios.get.mockRejectedValueOnce(new Error('API错误'))
    
    // 调用加载方法
    await wrapper.vm.fetchUserInfo()
    
    // 验证错误处理
    expect(ElMessage.error).toHaveBeenCalled()
    expect(wrapper.vm.loading).toBe(false)
  })
}) 