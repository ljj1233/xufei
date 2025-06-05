import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userAPI } from '../api/user'

// 测试模式下的默认账号
const DEFAULT_TEST_USER = {
  username: 'test_user',
  password: 'test123456',
  token: 'test_token_12345',
  id: '1'
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('user_token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const userId = ref(localStorage.getItem('user_id') || '')
  const userIsAdmin = ref(localStorage.getItem('user_is_admin') === 'true')
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userIsAdmin.value)
  
  // 设置认证头
  const getAuthHeaders = () => {
    return {
      headers: { Authorization: `Bearer ${token.value}` }
    }
  }
  
  // 登录方法
  const login = async (userData) => {
    try {
      console.log(`发送登录请求...`)
      const response = await userAPI.login(userData)
      if (response && response.access_token) {
        token.value = response.access_token
        // 获取用户信息
        await getUserInfo()
        
        // 保存到本地存储
        localStorage.setItem('user_token', token.value)
        
        return { success: true }
      }
      return { success: false, message: '登录失败' }
    } catch (error) {
      console.error('登录错误:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '登录失败，请检查网络连接'
      }
    }
  }
  
  // 注册方法
  const register = async (userData) => {
    try {
      console.log(`发送注册请求...`)
      console.log('注册数据:', userData)
      const response = await userAPI.register(userData)
      return { success: true, data: response }
    } catch (error) {
      console.error('注册错误:', error.response || error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '注册失败，请检查网络连接'
      }
    }
  }
  
  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await userAPI.getMe()
      username.value = response.username
      userId.value = response.id
      userIsAdmin.value = response.is_admin || false
      localStorage.setItem('username', username.value)
      localStorage.setItem('user_id', userId.value)
      localStorage.setItem('user_is_admin', userIsAdmin.value.toString())
      return { success: true, data: response }
    } catch (error) {
      if (error.response?.status === 401) {
        // 如果认证失败，清除登录状态
        logout()
      }
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取用户信息失败'
      }
    }
  }
  
  // 检查登录状态
  const checkLoginStatus = async () => {
    const mode = import.meta.env.VITE_APP_MODE || 'production'
    if (mode === 'test' && !token.value) {
      // 测试模式下自动登录
      token.value = DEFAULT_TEST_USER.token
      username.value = DEFAULT_TEST_USER.username
      userId.value = DEFAULT_TEST_USER.id
      localStorage.setItem('user_token', token.value)
      localStorage.setItem('username', username.value)
      localStorage.setItem('user_id', userId.value)
      return { success: true }
    } else if (token.value) {
      await getUserInfo()
    }
  }
  
  // 退出登录
  const logout = () => {
    token.value = ''
    username.value = ''
    userId.value = ''
    userIsAdmin.value = false
    localStorage.removeItem('user_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_is_admin')
  }
  
  // 修改密码
  const changePassword = async (passwordData) => {
    try {
      await userAPI.changePassword(passwordData)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '修改密码失败'
      }
    }
  }
  
  // 更新用户信息
  const updateUserInfo = async (userData) => {
    try {
      const response = await userAPI.updateProfile(userData)
      return { success: true, data: response }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '更新用户信息失败'
      }
    }
  }
  
  // 管理员API：获取所有用户
  const getUsers = async (page = 1, pageSize = 10) => {
    try {
      const response = await userAPI.getUsers(page, pageSize)
      return { 
        success: true, 
        data: {
          items: response.items,
          total: response.total
        }
      }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取用户列表失败'
      }
    }
  }
  
  // 管理员API：获取特定用户信息
  const getUserById = async (userId) => {
    try {
      const response = await userAPI.getUserById(userId)
      return { success: true, data: response }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取用户信息失败'
      }
    }
  }
  
  // 管理员API：更新用户状态
  const updateUserStatus = async (userId, isActive) => {
    try {
      const response = await userAPI.updateUserStatus(userId, isActive)
      return { success: true, data: response }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '更新用户状态失败'
      }
    }
  }
  
  // 管理员API：更新用户管理员权限
  const updateUserAdmin = async (userId, isAdmin) => {
    try {
      const response = await userAPI.updateUserAdmin(userId, isAdmin)
      return { success: true, data: response }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '更新用户管理员权限失败'
      }
    }
  }
  
  // 管理员API：删除用户
  const deleteUserById = async (userId) => {
    try {
      await userAPI.deleteUser(userId)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '删除用户失败'
      }
    }
  }
  
  return {
    token,
    username,
    userId,
    isLoggedIn,
    isAdmin,
    login,
    register,
    getUserInfo,
    checkLoginStatus,
    logout,
    changePassword,
    updateUserInfo,
    getAuthHeaders,
    // 管理员API
    getUsers,
    getUserById,
    updateUserStatus,
    updateUserAdmin,
    deleteUserById
  }
})