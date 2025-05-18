import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// 获取API基础URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

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
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  
  // 设置认证头
  const getAuthHeaders = () => {
    return {
      headers: { Authorization: `Bearer ${token.value}` }
    }
  }
  
  // 登录方法
  const login = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/users/login`, userData)
      if (response.data && response.data.access_token) {
        token.value = response.data.access_token
        // 获取用户信息
        await getUserInfo()
        
        // 保存到本地存储
        localStorage.setItem('user_token', token.value)
        
        return { success: true }
      }
      return { success: false, message: '登录失败' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '登录失败，请检查网络连接'
      }
    }
  }
  
  // 注册方法
  const register = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/users/register`, userData)
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '注册失败，请检查网络连接'
      }
    }
  }
  
  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/users/me`, getAuthHeaders())
      username.value = response.data.username
      userId.value = response.data.id
      localStorage.setItem('username', username.value)
      localStorage.setItem('user_id', userId.value)
      return { success: true, data: response.data }
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
    localStorage.removeItem('user_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
  }
  
  // 修改密码
  const changePassword = async (passwordData) => {
    try {
      const response = await axios.post(
        `${API_URL}/users/change-password`,
        passwordData,
        getAuthHeaders()
      )
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
      const response = await axios.put(
        `${API_URL}/users/update`,
        userData,
        getAuthHeaders()
      )
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '更新用户信息失败'
      }
    }
  }
  
  return {
    token,
    username,
    userId,
    isLoggedIn,
    login,
    register,
    getUserInfo,
    checkLoginStatus,
    logout,
    changePassword,
    updateUserInfo,
    getAuthHeaders
  }
})