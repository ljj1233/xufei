import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useInterviewStore } from '../../src/stores/interview'
import axios from 'axios'

// 模拟axios
vi.mock('axios')

describe('Interview Store', () => {
  beforeEach(() => {
    // 创建一个新的Pinia实例并使其激活
    setActivePinia(createPinia())
    // 重置所有模拟
    vi.resetAllMocks()
  })

  it('初始状态是正确的', () => {
    const store = useInterviewStore()
    expect(store.interviews).toEqual([])
    expect(store.currentInterview).toBeNull()
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchInterviews成功时更新interviews状态', async () => {
    // 模拟API响应
    const mockInterviews = [
      { id: 1, title: '测试面试1', status: 'completed' },
      { id: 2, title: '测试面试2', status: 'pending' }
    ]
    axios.get.mockResolvedValue({ data: mockInterviews })

    const store = useInterviewStore()
    await store.fetchInterviews()

    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(store.interviews).toEqual(mockInterviews)
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchInterviews失败时设置error状态', async () => {
    // 模拟API错误
    const errorMessage = '获取面试列表失败'
    axios.get.mockRejectedValue(new Error(errorMessage))

    const store = useInterviewStore()
    await store.fetchInterviews()

    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(store.interviews).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.error).toBe(errorMessage)
  })

  it('fetchInterviewDetail成功时更新currentInterview状态', async () => {
    // 模拟API响应
    const mockInterview = {
      id: 1,
      title: '测试面试',
      status: 'completed',
      analysis_results: {
        speech_text: '这是一段测试面试的回答',
        overall_score: 85
      }
    }
    axios.get.mockResolvedValue({ data: mockInterview })

    const store = useInterviewStore()
    await store.fetchInterviewDetail(1)

    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(store.currentInterview).toEqual(mockInterview)
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('uploadInterview成功时返回上传的面试', async () => {
    // 模拟API响应
    const mockUploadedInterview = {
      id: 3,
      title: '新上传的面试',
      status: 'pending'
    }
    axios.post.mockResolvedValue({ data: mockUploadedInterview })

    const store = useInterviewStore()
    const formData = new FormData()
    formData.append('title', '新上传的面试')
    
    const result = await store.uploadInterview(formData)

    expect(axios.post).toHaveBeenCalledTimes(1)
    expect(result).toEqual(mockUploadedInterview)
    expect(store.isLoading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('uploadInterview失败时设置error状态', async () => {
    // 模拟API错误
    const errorMessage = '上传面试失败'
    axios.post.mockRejectedValue(new Error(errorMessage))

    const store = useInterviewStore()
    const formData = new FormData()
    formData.append('title', '新上传的面试')
    
    try {
      await store.uploadInterview(formData)
    } catch (error) {
      expect(error.message).toBe(errorMessage)
    }

    expect(axios.post).toHaveBeenCalledTimes(1)
    expect(store.isLoading).toBe(false)
    expect(store.error).toBe(errorMessage)
  })
})