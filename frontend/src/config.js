/**
 * 配置文件
 * 
 * 包含全局配置和API URL
 */

// API基础URL
export const API_URL = 'http://localhost:8000/api/v1';

// 默认配置
export const CONFIG = {
  // API相关
  apiUrl: API_URL,
  
  // 上传文件相关
  uploadMaxSize: 500 * 1024 * 1024, // 500MB
  
  // 开发模式配置
  isDevelopment: import.meta.env.DEV,
  isTestMode: import.meta.env.VITE_APP_MODE === 'test'
}; 