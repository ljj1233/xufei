import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useUserStore } from './user'

// 获取API基础URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const useInterviewStore = defineStore('interview', () => {
  // 状态
  const interviews = ref([])
  const currentInterview = ref(null)
  const currentAnalysis = ref(null)
  const isLoading = ref(false)
  
  // 获取用户store
  const userStore = useUserStore()
  
  // 获取面试列表
  const getInterviews = async () => {
    isLoading.value = true
    try {
      const response = await axios.get(
        `${API_URL}/interviews`,
        userStore.getAuthHeaders()
      )
      interviews.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取面试列表失败'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取面试详情
  const getInterviewById = async (id) => {
    isLoading.value = true
    try {
      const response = await axios.get(
        `${API_URL}/interviews/${id}`,
        userStore.getAuthHeaders()
      )
      currentInterview.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取面试详情失败'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取分析结果
  const getAnalysisById = async (id) => {
    isLoading.value = true
    try {
      const response = await axios.get(
        `${API_URL}/analysis/${id}`,
        userStore.getAuthHeaders()
      )
      currentAnalysis.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取分析结果失败'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  // 上传面试文件
  const uploadInterview = async (formData) => {
    isLoading.value = true
    try {
      const response = await axios.post(
        `${API_URL}/interviews/upload/`,
        formData,
        {
          ...userStore.getAuthHeaders(),
          headers: {
            ...userStore.getAuthHeaders().headers,
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '上传面试失败'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  // 开始分析
  const startAnalysis = async (id) => {
    isLoading.value = true
    try {
      const response = await axios.post(
        `${API_URL}/analysis/${id}`,
        {},
        userStore.getAuthHeaders()
      )
      currentAnalysis.value = response.data
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '开始分析失败'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取职位列表
  const getJobPositions = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/job-positions`,
        userStore.getAuthHeaders()
      )
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '获取职位列表失败'
      }
    }
  }
  
  // 创建新职位
  const createJobPosition = async (positionData) => {
    try {
      const response = await axios.post(
        `${API_URL}/job-positions`,
        positionData,
        userStore.getAuthHeaders()
      )
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '创建职位失败'
      }
    }
  }
  
  return {
    interviews,
    currentInterview,
    currentAnalysis,
    isLoading,
    getInterviews,
    getInterviewById,
    getAnalysisById,
    uploadInterview,
    startAnalysis,
    getJobPositions,
    createJobPosition
  }
})