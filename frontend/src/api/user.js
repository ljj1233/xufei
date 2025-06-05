import axios from 'axios'
import { useUserStore } from '../stores/user'
import { API_URL } from '../config'

// 创建axios实例
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API错误:', error.response?.data || error.message)
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 用户API
export const userAPI = {
  // 登录
  login: async (userData) => {
    const formData = new FormData()
    formData.append('username', userData.username)
    formData.append('password', userData.password)
    
    const response = await axios.post(`${API_URL}/users/login`, formData)
    return response.data
  },
  
  // 注册
  register: async (userData) => {
    const response = await api.post('/users/register', userData)
    return response.data
  },
  
  // 获取当前用户信息
  getMe: async () => {
    const response = await api.get('/users/me')
    return response.data
  },
  
  // 更新用户信息
  updateProfile: async (userData) => {
    const response = await api.put('/users/me', userData)
    return response.data
  },
  
  // 修改密码
  changePassword: async (passwordData) => {
    const response = await api.post('/users/change-password', passwordData)
    return response.data
  },
  
  // 获取用户统计信息
  getStats: async () => {
    const response = await api.get('/users/stats')
    return response.data
  },
  
  // 管理员API：获取所有用户
  getUsers: async (page = 1, pageSize = 10) => {
    const response = await api.get(`/users?skip=${(page-1)*pageSize}&limit=${pageSize}`)
    return {
      items: response.data,
      total: parseInt(response.headers['x-total-count'] || response.data.length)
    }
  },
  
  // 管理员API：获取特定用户
  getUserById: async (userId) => {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },
  
  // 管理员API：更新用户状态
  updateUserStatus: async (userId, isActive) => {
    const response = await api.patch(`/users/${userId}/status`, { is_active: isActive })
    return response.data
  },
  
  // 管理员API：更新用户管理员权限
  updateUserAdmin: async (userId, isAdmin) => {
    const response = await api.patch(`/users/${userId}/admin`, { is_admin: isAdmin })
    return response.data
  },
  
  // 管理员API：删除用户
  deleteUser: async (userId) => {
    const response = await api.delete(`/users/${userId}`)
    return response.data
  }
} 