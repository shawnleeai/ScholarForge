/**
 * 认证服务 API
 */

import { request } from './api'
import { mockApi } from './mockApi'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '@/types'

// 是否使用模拟API（开发时可设置为true）
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || false

export const authService = {
  /**
   * 用户登录
   */
  login: async (data: LoginRequest) => {
    if (USE_MOCK) {
      return mockApi.post('/auth/login', data) as { data: AuthResponse }
    }
    const response = await request.post<AuthResponse>('/auth/login', data)
    return { data: response.data }
  },

  /**
   * 用户注册
   */
  register: async (data: RegisterRequest) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      const response = {
        code: 200,
        data: {
          user: {
            id: Date.now().toString(),
            email: data.email,
            username: data.username,
            role: 'student',
            fullName: data.fullName || '',
            university: data.university || '',
            major: data.major || '',
            subscriptionTier: 'free',
            isActive: true,
            isVerified: false,
            createdAt: new Date().toISOString(),
          },
          token: {
            accessToken: `mock-token-${Date.now()}`,
            refreshToken: `mock-refresh-${Date.now()}`,
            tokenType: 'Bearer',
            expiresIn: 86400,
          },
        },
      }
      return response as { data: AuthResponse }
    }
    const response = await request.post<AuthResponse>('/auth/register', data)
    return { data: response.data }
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser: async () => {
    if (USE_MOCK) {
      return mockApi.get('/users/me') as { data: User }
    }
    const response = await request.get<User>('/users/me')
    return { data: response.data }
  },

  /**
   * 刷新Token
   */
  refreshToken: async (refreshToken: string) => {
    if (USE_MOCK) {
      return {
        data: {
          accessToken: `mock-token-${Date.now()}`,
          refreshToken: `mock-refresh-${Date.now()}`,
          tokenType: 'Bearer',
          expiresIn: 86400,
        }
      }
    }
    const response = await request.post('/auth/refresh', { refresh_token: refreshToken })
    return { data: response.data }
  },

  /**
   * 用户登出
   */
  logout: async () => {
    if (USE_MOCK) {
      localStorage.removeItem('scholarforge-auth')
      return { code: 200 }
    }
    return request.post('/auth/logout')
  },

  /**
   * 修改密码
   */
  changePassword: async (oldPassword: string, newPassword: string) => {
    if (USE_MOCK) {
      return { code: 200, message: '密码修改成功' }
    }
    return request.post('/users/me/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },

  /**
   * 更新用户信息
   */
  updateProfile: async (data: Partial<User>) => {
    if (USE_MOCK) {
      return { code: 200, data }
    }
    const response = await request.put<User>('/users/me', data)
    return { data: response.data }
  },
}
