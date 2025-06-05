<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-header height="60px">
          <div class="header-content">
            <div class="logo">
              <router-link to="/">
                <h1>多模态面试评测智能体</h1>
              </router-link>
            </div>
            <div class="nav-menu" v-if="userStore.isLoggedIn">
              <el-menu
                :default-active="activeIndex"
                mode="horizontal"
                router
                background-color="#545c64"
                text-color="#fff"
                active-text-color="#ffd04b"
                class="main-menu"
              >
                <el-menu-item index="/">首页</el-menu-item>
                <el-menu-item index="/upload">上传面试</el-menu-item>
                <el-menu-item index="/results">面试结果</el-menu-item>
                <el-menu-item index="/interview-practice">模拟面试</el-menu-item>
                <el-menu-item index="/practice-history">练习记录</el-menu-item>
                <el-menu-item index="/user">个人中心</el-menu-item>
                <el-menu-item v-if="userStore.isAdmin" index="/admin">管理控制台</el-menu-item>
                <el-menu-item @click="logout">退出登录</el-menu-item>
              </el-menu>
            </div>
            <div class="user-actions">
              <template v-if="userStore.isLoggedIn">
                <el-dropdown>
                  <span class="user-dropdown">
                    {{ userStore.username }}
                    <el-icon><arrow-down /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="router.push('/user')">个人中心</el-dropdown-item>
                      <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
              <template v-else>
                <el-button type="primary" @click="router.push('/login')">登录</el-button>
                <el-button @click="router.push('/register')">注册</el-button>
              </template>
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
        <el-footer height="60px">
          <div class="footer-content">
            <p>© {{ new Date().getFullYear() }} 多模态面试评测智能体 - 基于Vue.js和Element Plus构建</p>
          </div>
        </el-footer>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/user'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const router = useRouter()
const userStore = useUserStore()
const route = useRoute()

// 计算当前激活的导航项
const activeIndex = computed(() => route.path)

// 退出登录
const logout = () => {
  userStore.logout()
  ElMessage.success('退出登录成功')
  router.push('/')
}

// 组件挂载时检查登录状态
onMounted(async () => {
  await userStore.checkLoginStatus()
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-container {
  min-height: 100vh;
}

.el-header {
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.logo h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1E88E5;
}

.logo a {
  text-decoration: none;
  color: inherit;
}

.nav-menu {
  flex-grow: 1;
  margin: 0 20px;
}

.user-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}

.el-footer {
  background-color: #ffffff;
  border-top: 1px solid #e6e6e6;
}

.footer-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #606266;
}

.main-menu {
  margin-bottom: 20px;
}

.main-content {
  flex: 1;
  padding: 0 20px;
}

.app-footer {
  background-color: #f5f5f5;
  padding: 20px;
  text-align: center;
  margin-top: 30px;
}
</style>