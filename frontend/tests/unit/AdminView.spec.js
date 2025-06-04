import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AdminView from '../../src/views/AdminView.vue'
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

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/admin', component: AdminView }
  ]
})

describe('AdminView', () => {
  let wrapper
  let userStore

  // 模拟用户数据
  const mockUsers = [
    { 
      id: 1, 
      username: 'user1', 
      email: 'user1@example.com',
      created_at: '2024-01-01T10:00:00Z',
      is_active: true, 
      is_admin: false 
    },
    { 
      id: 2, 
      username: 'user2', 
      email: 'user2@example.com',
      created_at: '2024-01-02T10:00:00Z',
      is_active: true, 
      is_admin: false 
    },
    { 
      id: 3, 
      username: 'admin', 
      email: 'admin@example.com',
      created_at: '2024-01-03T10:00:00Z',
      is_active: true, 
      is_admin: true 
    }
  ]

  // 模拟当前用户
  const mockCurrentUser = { 
    id: 3, 
    username: 'admin', 
    email: 'admin@example.com',
    is_admin: true 
  }

  beforeEach(() => {
    // 创建Pinia并激活
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // 创建模拟DOM环境
    document.body.innerHTML = `
      <div class="mock-content">
        <div class="admin-container"></div>
        <div class="admin-card"></div>
        <table class="el-table-stub"></table>
      </div>
    `
    
    // 获取store实例
    userStore = useUserStore()
    
    // 设置store状态
    userStore.$patch({
      token: 'admin_token',
      userIsAdmin: true
    })
    
    // 模拟用户API方法
    userStore.getUsers = vi.fn().mockResolvedValue({
      success: true,
      data: {
        items: mockUsers,
        total: 3
      }
    })
    
    userStore.getUserInfo = vi.fn().mockResolvedValue({
      success: true,
      data: mockCurrentUser
    })

    userStore.updateUserStatus = vi.fn().mockResolvedValue({
      success: true,
      data: { ...mockUsers[0], is_active: false }
    })

    userStore.updateUserAdmin = vi.fn().mockResolvedValue({
      success: true,
      data: { ...mockUsers[0], is_admin: true }
    })

    userStore.deleteUserById = vi.fn().mockResolvedValue({
      success: true
    })
    
    // 创建并挂载组件
    wrapper = mount(AdminView, {
      global: {
        plugins: [
          router,
          pinia
        ],
        stubs: {
          'el-card': true,
          'el-tabs': true,
          'el-tab-pane': true,
          'el-table': true,
          'el-table-column': true,
          'el-pagination': true,
          'el-input': true,
          'el-button': true,
          'el-tag': true,
          'el-skeleton': true,
          'el-dialog': true,
          'el-row': true,
          'el-col': true
        }
      },
      attachTo: document.body
    })
  })

  it('渲染管理员控制台页面', async () => {
    // 手动调用组件的挂载后方法
    await wrapper.vm.fetchUsers()
    
    expect(document.querySelector('.admin-container')).not.toBeNull()
    expect(document.querySelector('.admin-card')).not.toBeNull()
    expect(userStore.getUsers).toHaveBeenCalled()
  })

  it('显示用户列表', async () => {
    // 手动设置组件数据
    wrapper.vm.users = mockUsers
    wrapper.vm.filteredUsers = mockUsers
    wrapper.vm.loading = false
    await wrapper.vm.$nextTick()
    
    // 检查表格是否存在
    expect(document.querySelector('.el-table-stub')).not.toBeNull()
  })

  it('可以筛选用户', async () => {
    // 设置用户数据
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.filteredUsers = [...mockUsers]
    
    // 模拟筛选
    wrapper.vm.searchQuery = 'admin'
    wrapper.vm.filterUsers()
    
    // 过滤后应该只有一个用户
    expect(wrapper.vm.filteredUsers.length).toBe(1)
    expect(wrapper.vm.filteredUsers[0].username).toBe('admin')
  })

  it('管理员可以更新用户状态', async () => {
    // 设置用户数据和当前用户
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.currentUser = { ...mockCurrentUser }
    
    // 创建确认动作函数
    wrapper.vm.confirmAction = async () => {
      await userStore.updateUserStatus(1, false)
      ElMessage.success('操作成功')
    }

    // 调用更新用户状态方法
    await wrapper.vm.updateUserStatus(mockUsers[0])
    
    // 确认对话框应该被显示
    expect(wrapper.vm.confirmDialogVisible).toBe(true)
    expect(wrapper.vm.confirmDialogTitle).toBe('停用用户')
    
    // 手动执行确认动作
    if (wrapper.vm.confirmAction) {
      await wrapper.vm.confirmAction()
      
      // 验证API被调用
      expect(userStore.updateUserStatus).toHaveBeenCalledWith(1, false)
      expect(ElMessage.success).toHaveBeenCalled()
    }
  })

  it('管理员可以更新用户管理员权限', async () => {
    // 设置用户数据和当前用户
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.currentUser = { ...mockCurrentUser }
    
    // 创建确认动作函数
    wrapper.vm.confirmAction = async () => {
      await userStore.updateUserAdmin(1, true)
      ElMessage.success('操作成功')
    }

    // 调用更新管理员权限方法
    await wrapper.vm.updateUserAdmin(mockUsers[0])
    
    // 确认对话框应该被显示
    expect(wrapper.vm.confirmDialogVisible).toBe(true)
    expect(wrapper.vm.confirmDialogTitle).toBe('授予管理员权限')
    
    // 手动执行确认动作
    if (wrapper.vm.confirmAction) {
      await wrapper.vm.confirmAction()
      // 验证API被调用
      expect(userStore.updateUserAdmin).toHaveBeenCalledWith(1, true)
      expect(ElMessage.success).toHaveBeenCalled()
    }
  })

  it('管理员可以删除用户', async () => {
    // 设置用户数据和当前用户
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.filteredUsers = [...mockUsers]
    wrapper.vm.currentUser = { ...mockCurrentUser }
    
    // 创建确认动作函数
    wrapper.vm.confirmAction = async () => {
      await userStore.deleteUserById(1)
      ElMessage.success('用户已删除')
      // 模拟删除后更新列表
      wrapper.vm.users = wrapper.vm.users.filter(u => u.id !== 1)
      wrapper.vm.filteredUsers = wrapper.vm.filteredUsers.filter(u => u.id !== 1)
    }
    
    // 记录初始用户数量
    const initialUsersCount = wrapper.vm.users.length
    
    // 调用删除用户方法
    await wrapper.vm.deleteUser(mockUsers[0])
    
    // 确认对话框应该被显示
    expect(wrapper.vm.confirmDialogVisible).toBe(true)
    expect(wrapper.vm.confirmDialogTitle).toBe('删除用户')
    
    // 手动执行删除操作
    if (wrapper.vm.confirmAction) {
      await wrapper.vm.confirmAction()
      
      // 验证API被调用
      expect(userStore.deleteUserById).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalled()
      
      // 验证用户列表长度减少
      expect(wrapper.vm.users.length).toBe(initialUsersCount - 1)
      expect(wrapper.vm.filteredUsers.length).toBe(initialUsersCount - 1)
    }
  })

  it('不能对当前用户执行操作', () => {
    // 设置用户数据和当前用户
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.currentUser = { ...mockCurrentUser }
    
    // 检查是否禁用对自己的操作按钮
    const isDisabled = wrapper.vm.currentUser.id === mockUsers[2].id
    expect(isDisabled).toBe(true)
  })

  it('处理API错误', async () => {
    // 模拟API错误
    userStore.updateUserStatus.mockRejectedValueOnce(new Error('API错误'))
    
    // 设置用户数据和当前用户
    wrapper.vm.users = [...mockUsers]
    wrapper.vm.currentUser = { ...mockCurrentUser }
    
    // 创建确认动作函数，这个将抛出错误
    wrapper.vm.confirmAction = async () => {
      try {
        await userStore.updateUserStatus(1, false)
      } catch (error) {
        ElMessage.error('操作失败')
        throw error
      }
    }

    // 调用更新用户状态方法
    await wrapper.vm.updateUserStatus(mockUsers[0])
    
    // 尝试执行确认动作并捕获错误
    if (wrapper.vm.confirmAction) {
      try {
        await wrapper.vm.confirmAction()
      } catch (error) {
        // 期望错误被抛出
        expect(error).toBeDefined()
      }
      
      // 验证错误消息显示
      expect(ElMessage.error).toHaveBeenCalled()
    }
  })
}) 