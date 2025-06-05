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

// 职位API
export const jobPositionAPI = {
  // 获取所有职位
  getAllPositions: async (params = {}) => {
    const response = await api.get('/job-positions/', { params })
    return response.data
  },

  // 获取职位详情
  getPositionById: async (id) => {
    const response = await api.get(`/job-positions/${id}`)
    return response.data
  },

  // 创建职位
  createPosition: async (data) => {
    const response = await api.post('/job-positions/', data)
    return response.data
  },

  // 更新职位
  updatePosition: async (id, data) => {
    const response = await api.put(`/job-positions/${id}`, data)
    return response.data
  },

  // 删除职位
  deletePosition: async (id) => {
    const response = await api.delete(`/job-positions/${id}`)
    return response.data
  },

  // 获取技术领域列表
  getTechFields: async () => {
    const response = await api.get('/job-positions/tech-fields')
    return response.data
  },
  
  // 获取职位类型列表
  getPositionTypes: async () => {
    const response = await api.get('/job-positions/position-types')
    return response.data
  }
} 