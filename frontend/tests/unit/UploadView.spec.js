import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import UploadView from '../../src/views/UploadView.vue'
import { useInterviewStore } from '../../src/stores/interview'
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
    { path: '/results', component: { template: '<div>Results</div>' } },
    { path: '/upload', component: UploadView }
  ]
})

describe('UploadView', () => {
  let wrapper
  let store

  beforeEach(() => {
    // 创建测试Pinia并挂载组件
    wrapper = mount(UploadView, {
      global: {
        plugins: [
          router,
          createTestingPinia({
            createSpy: vi.fn,
            stubActions: false
          })
        ],
        stubs: {
          'el-upload': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'el-alert': true
        }
      }
    })

    // 获取store实例
    store = useInterviewStore()
    // 模拟uploadInterview方法
    store.uploadInterview = vi.fn()
  })

  it('渲染上传表单', () => {
    expect(wrapper.find('.upload-container').exists()).toBe(true)
    expect(wrapper.find('.page-title').text()).toBe('上传面试视频/音频')
  })

  it('表单验证失败时不提交', async () => {
    // 模拟表单验证失败
    wrapper.vm.$refs.uploadFormRef = {
      validate: vi.fn((callback) => callback(false))
    }

    // 触发表单提交
    await wrapper.vm.submitUpload()

    // 验证store方法未被调用
    expect(store.uploadInterview).not.toHaveBeenCalled()
  })

  it('表单验证成功时提交并处理成功响应', async () => {
    // 模拟表单验证成功
    wrapper.vm.$refs.uploadFormRef = {
      validate: vi.fn((callback) => callback(true))
    }

    // 模拟文件上传
    const file = new File(['test'], 'test.mp3', { type: 'audio/mpeg' })
    wrapper.vm.uploadFile = file

    // 模拟store返回成功响应
    store.uploadInterview.mockResolvedValue({ id: 1, title: '测试面试' })

    // 触发表单提交
    await wrapper.vm.submitUpload()

    // 验证store方法被调用
    expect(store.uploadInterview).toHaveBeenCalled()
    // 验证成功消息被显示
    expect(ElMessage.success).toHaveBeenCalled()
    // 验证路由跳转
    expect(router.currentRoute.value.path).toBe('/results')
  })

  it('处理上传失败', async () => {
    // 模拟表单验证成功
    wrapper.vm.$refs.uploadFormRef = {
      validate: vi.fn((callback) => callback(true))
    }

    // 模拟文件上传
    const file = new File(['test'], 'test.mp3', { type: 'audio/mpeg' })
    wrapper.vm.uploadFile = file

    // 模拟store返回失败
    const error = new Error('上传失败')
    store.uploadInterview.mockRejectedValue(error)

    // 触发表单提交
    await wrapper.vm.submitUpload()

    // 验证错误消息被显示
    expect(ElMessage.error).toHaveBeenCalledWith('上传失败：上传失败')
    // 验证加载状态被重置
    expect(wrapper.vm.isUploading).toBe(false)
  })
})