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
  const error = ref(null)
  
  // 获取用户store
  const userStore = useUserStore()
  
  // 获取面试列表
  const getInterviews = async (jobPositionId = null) => {
    isLoading.value = true
    error.value = null
    
    try {
      const params = jobPositionId ? { job_position_id: jobPositionId } : {}
      const response = await axios.get(
        `${API_URL}/interviews`,
        {
          params,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      interviews.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '获取面试列表失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取单个面试详情
  const getInterview = async (id) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.get(
        `${API_URL}/interviews/${id}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      currentInterview.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '获取面试详情失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取面试分析结果
  const getInterviewAnalysis = async (id) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.get(
        `${API_URL}/interviews/${id}/analyze`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      currentAnalysis.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '获取分析结果失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 上传面试文件
  const uploadInterview = async (formData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post(
        `${API_URL}/interviews/upload/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '上传面试失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 分析面试
  const analyzeInterview = async (id) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post(
        `${API_URL}/interviews/${id}/analyze`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      currentAnalysis.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '分析面试失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 获取职位列表
  const getJobPositions = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.get(
        `${API_URL}/job-positions`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '获取职位列表失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  // 创建职位
  const createJobPosition = async (jobPositionData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.post(
        `${API_URL}/job-positions`,
        jobPositionData,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('user_token')}`
          }
        }
      )
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '创建职位失败'
      throw error.value
    } finally {
      isLoading.value = false
    }
  }
  
  return {
    interviews,
    currentInterview,
    currentAnalysis,
    isLoading,
    error,
    getInterviews,
    getInterview,
    getInterviewAnalysis,
    uploadInterview,
    analyzeInterview,
    getJobPositions,
    createJobPosition
  }
})