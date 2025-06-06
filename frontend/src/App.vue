<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-header height="60px">
          <div class="header-content">
            <div class="logo">
              <router-link to="/">
                <img src="./assets/logo.svg" alt="Logo" class="logo-image" />
                <h1>多模态面试评测系统</h1>
              </router-link>
            </div>
            <div class="nav-menu" v-if="userStore.isLoggedIn">
              <el-menu
                :default-active="activeIndex"
                mode="horizontal"
                router
                class="main-menu"
              >
                <el-menu-item index="/">
                  <icon-home class="nav-icon" />
                  <span>首页</span>
                </el-menu-item>
                <el-menu-item index="/upload">
                  <icon-upload class="nav-icon" />
                  <span>上传面试</span>
                </el-menu-item>
                <el-menu-item index="/interview-practice">
                  <icon-practice class="nav-icon" />
                  <span>模拟面试</span>
                </el-menu-item>
                <el-menu-item index="/practice-history">
                  <icon-history class="nav-icon" />
                  <span>练习记录</span>
                </el-menu-item>
                <el-menu-item index="/user">
                  <icon-user class="nav-icon" />
                  <span>个人中心</span>
                </el-menu-item>
                <el-menu-item v-if="userStore.isAdmin" index="/admin">
                  <icon-admin class="nav-icon" />
                  <span>管理控制台</span>
                </el-menu-item>
              </el-menu>
            </div>
            <div class="user-actions">
              <template v-if="userStore.isLoggedIn">
                <el-dropdown>
                  <span class="user-dropdown">
                    <el-avatar :size="32" :src="avatarUrl" />
                    {{ userStore.username }}
                    <el-icon><arrow-down /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="router.push('/user')">
                        <icon-user class="dropdown-icon" /> 个人中心
                      </el-dropdown-item>
                      <el-dropdown-item @click="router.push('/interview-practice')">
                        <icon-practice class="dropdown-icon" /> 开始面试
                      </el-dropdown-item>
                      <el-dropdown-item divided @click="logout">
                        <el-icon><SwitchButton /></el-icon> 退出登录
                      </el-dropdown-item>
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
            <div class="footer-links">
              <a href="#">隐私政策</a>
              <a href="#">使用条款</a>
              <a href="#">帮助中心</a>
              <a href="#">联系我们</a>
            </div>
            <p>© {{ new Date().getFullYear() }} 多模态面试评测系统 - 企业级面试训练与评估平台</p>
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
import { ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 导入SVG图标组件
import IconHome from './components/icons/IconHome.vue'
import IconUpload from './components/icons/IconUpload.vue'
import IconPractice from './components/icons/IconPractice.vue'
import IconHistory from './components/icons/IconHistory.vue'
import IconUser from './components/icons/IconUser.vue'
import IconAdmin from './components/icons/IconAdmin.vue'

const router = useRouter()
const userStore = useUserStore()
const route = useRoute()

// 默认头像URL
const avatarUrl = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 计算当前激活的导航项
const activeIndex = computed(() => route.path)

// 退出登录
const logout = () => {
  userStore.logout()
  ElMessage.success('退出登录成功')
  router.push('/login')
}

// 组件挂载时检查登录状态
onMounted(async () => {
  try {
    console.log('检查登录状态...')
    const result = await userStore.checkLoginStatus()
    console.log('登录状态检查结果:', result.success ? '已登录' : '未登录')
    
    // 如果当前路由需要认证但未登录，重定向到登录页
    if (!result.success && route.meta.requiresAuth) {
      console.log('需要登录，重定向到登录页')
      router.push('/login')
    }
  } catch (error) {
    console.error('检查登录状态出错:', error)
    // 发生错误时清除登录状态
    userStore.logout()
    if (route.meta.requiresAuth) {
      router.push('/login')
    }
  }
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
  background-color: var(--bg-primary);
  box-shadow: var(--box-shadow-light);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
}

.logo h1 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--primary-color);
  font-weight: 500;
}

.logo-image {
  height: 32px;
  margin-right: 10px;
}

.logo a {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
}

.nav-menu {
  flex-grow: 1;
  margin: 0 20px;
}

/* 企业风格导航菜单 */
.main-menu.el-menu--horizontal {
  border-bottom: none;
}

.main-menu.el-menu--horizontal .el-menu-item {
  font-size: 14px;
  height: 60px;
  line-height: 60px;
  border-bottom: 2px solid transparent;
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-menu.el-menu--horizontal .el-menu-item.is-active {
  color: var(--primary-color);
  border-bottom: 2px solid var(--primary-color);
}

.main-menu.el-menu--horizontal .el-menu-item.is-active .nav-icon {
  color: var(--primary-color);
}

.nav-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
}

.dropdown-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  vertical-align: middle;
}

.user-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: var(--border-radius-base);
  transition: background-color 0.2s;
  user-select: none;
}

.user-dropdown:hover {
  background-color: var(--bg-secondary);
}

.el-main {
  padding: 20px;
  background-color: var(--bg-secondary);
}

.el-footer {
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-light);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: var(--text-secondary);
}

.footer-links {
  display: flex;
  gap: 20px;
  margin-bottom: 8px;
}

.footer-links a {
  color: var(--primary-color);
  text-decoration: none;
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }
  
  .header-content {
    padding: 0 10px;
  }
  
  .logo h1 {
    font-size: 1rem;
  }
}
</style>