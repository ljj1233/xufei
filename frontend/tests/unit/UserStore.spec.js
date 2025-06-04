import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../../src/stores/user'
import axios from 'axios'

// 模拟axios
vi.mock('axios')

describe('User Store', () => {
  beforeEach(() => {
    // 创建一个新的Pinia实例并使其激活
    setActivePinia(createPinia())
    // 重置所有模拟
    vi.resetAllMocks()
    // 清除localStorage
    localStorage.clear()
  })

  it('初始状态是正确的', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.username).toBe('')
    expect(store.userId).toBe('')
    expect(store.isLoggedIn).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  describe('登录功能', () => {
    it('登录成功时设置token并获取用户信息', async () => {
      // 模拟登录成功响应
      const mockToken = 'test_token_123'
      axios.post.mockResolvedValueOnce({ data: { access_token: mockToken } })
      
      // 模拟获取用户信息响应
      const mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        is_admin: false
      }
      axios.get.mockResolvedValueOnce({ data: mockUser })
      
      const store = useUserStore()
      const result = await store.login({ username: 'testuser', password: 'password123' })
      
      expect(result.success).toBe(true)
      expect(store.token).toBe(mockToken)
      expect(store.username).toBe(mockUser.username)
      expect(store.userId).toBe(mockUser.id)
      expect(localStorage.getItem('user_token')).toBe(mockToken)
      expect(store.isLoggedIn).toBe(true)
      expect(store.isAdmin).toBe(false)
    })
    
    it('登录失败时返回错误信息', async () => {
      // 模拟登录失败响应
      axios.post.mockRejectedValueOnce({
        response: { data: { detail: '用户名或密码错误' } }
      })
      
      const store = useUserStore()
      const result = await store.login({ username: 'testuser', password: 'wrongpassword' })
      
      expect(result.success).toBe(false)
      expect(result.message).toBe('用户名或密码错误')
      expect(store.token).toBe('')
      expect(store.isLoggedIn).toBe(false)
    })
  })

  describe('注册功能', () => {
    it('注册成功时返回用户数据', async () => {
      // 模拟注册成功响应
      const mockUser = {
        id: '1',
        username: 'newuser',
        email: 'new@example.com'
      }
      axios.post.mockResolvedValueOnce({ data: mockUser })
      
      const store = useUserStore()
      const result = await store.register({ 
        username: 'newuser', 
        email: 'new@example.com', 
        password: 'password123' 
      })
      
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockUser)
    })
    
    it('注册失败时返回错误信息', async () => {
      // 模拟注册失败响应
      axios.post.mockRejectedValueOnce({
        response: { data: { detail: '用户名已存在' } }
      })
      
      const store = useUserStore()
      const result = await store.register({ 
        username: 'existinguser', 
        email: 'existing@example.com', 
        password: 'password123' 
      })
      
      expect(result.success).toBe(false)
      expect(result.message).toBe('用户名已存在')
    })
  })

  describe('获取用户信息', () => {
    it('获取用户信息成功时更新用户状态', async () => {
      // 先设置token
      const store = useUserStore()
      store.token = 'some_token'
      
      // 模拟获取用户信息响应
      const mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        is_admin: true
      }
      axios.get.mockResolvedValueOnce({ data: mockUser })
      
      const result = await store.getUserInfo()
      
      expect(result.success).toBe(true)
      expect(store.username).toBe(mockUser.username)
      expect(store.userId).toBe(mockUser.id)
      expect(localStorage.getItem('username')).toBe(mockUser.username)
      expect(localStorage.getItem('user_id')).toBe(mockUser.id)
      expect(store.isAdmin).toBe(true)
      expect(localStorage.getItem('user_is_admin')).toBe('true')
    })
    
    it('获取用户信息失败时清除登录状态', async () => {
      // 设置初始状态
      const store = useUserStore()
      store.token = 'some_token'
      store.username = 'testuser'
      store.userId = '1'
      localStorage.setItem('user_token', 'some_token')
      localStorage.setItem('username', 'testuser')
      localStorage.setItem('user_id', '1')
      
      // 模拟401错误响应
      axios.get.mockRejectedValueOnce({
        response: { status: 401, data: { detail: 'Token已失效' } }
      })
      
      const result = await store.getUserInfo()
      
      expect(result.success).toBe(false)
      expect(result.message).toBe('Token已失效')
      expect(store.token).toBe('')
      expect(store.username).toBe('')
      expect(store.userId).toBe('')
      expect(localStorage.getItem('user_token')).toBeNull()
      expect(localStorage.getItem('username')).toBeNull()
      expect(localStorage.getItem('user_id')).toBeNull()
    })
  })

  describe('退出登录', () => {
    it('退出登录时清除所有用户状态', () => {
      // 设置初始状态
      const store = useUserStore()
      store.token = 'some_token'
      store.username = 'testuser'
      store.userId = '1'
      localStorage.setItem('user_token', 'some_token')
      localStorage.setItem('username', 'testuser')
      localStorage.setItem('user_id', '1')
      localStorage.setItem('user_is_admin', 'true')
      
      store.logout()
      
      expect(store.token).toBe('')
      expect(store.username).toBe('')
      expect(store.userId).toBe('')
      expect(localStorage.getItem('user_token')).toBeNull()
      expect(localStorage.getItem('username')).toBeNull()
      expect(localStorage.getItem('user_id')).toBeNull()
      expect(localStorage.getItem('user_is_admin')).toBeNull()
      expect(store.isLoggedIn).toBe(false)
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('管理员API', () => {
    beforeEach(() => {
      // 设置为管理员用户
      const store = useUserStore()
      store.token = 'admin_token'
      localStorage.setItem('user_is_admin', 'true')
    })

    it('获取用户列表成功', async () => {
      // 模拟获取用户列表响应
      const mockUsers = [
        { id: 1, username: 'user1', email: 'user1@example.com', is_admin: false },
        { id: 2, username: 'user2', email: 'user2@example.com', is_admin: false },
        { id: 3, username: 'admin', email: 'admin@example.com', is_admin: true }
      ]
      axios.get.mockResolvedValueOnce({ 
        data: mockUsers, 
        headers: { 'x-total-count': '10' } 
      })
      
      const store = useUserStore()
      const result = await store.getUsers(1, 3)
      
      expect(result.success).toBe(true)
      expect(result.data.items).toEqual(mockUsers)
      expect(result.data.total).toBe('10')
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringMatching(/users\?skip=0&limit=3/),
        expect.anything()
      )
    })

    it('更新用户状态成功', async () => {
      // 模拟更新用户状态响应
      const mockUser = { id: 1, username: 'user1', is_active: false }
      axios.patch.mockResolvedValueOnce({ data: mockUser })
      
      const store = useUserStore()
      const result = await store.updateUserStatus(1, false)
      
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockUser)
      expect(axios.patch).toHaveBeenCalledWith(
        expect.stringMatching(/users\/1\/status/),
        { is_active: false },
        expect.anything()
      )
    })

    it('更新用户管理员权限成功', async () => {
      // 模拟更新管理员权限响应
      const mockUser = { id: 1, username: 'user1', is_admin: true }
      axios.patch.mockResolvedValueOnce({ data: mockUser })
      
      const store = useUserStore()
      const result = await store.updateUserAdmin(1, true)
      
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockUser)
      expect(axios.patch).toHaveBeenCalledWith(
        expect.stringMatching(/users\/1\/admin/),
        { is_admin: true },
        expect.anything()
      )
    })

    it('删除用户成功', async () => {
      // 模拟删除用户响应
      axios.delete.mockResolvedValueOnce({ status: 200 })
      
      const store = useUserStore()
      const result = await store.deleteUserById(1)
      
      expect(result.success).toBe(true)
      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringMatching(/users\/1/),
        expect.anything()
      )
    })
  })
}) 