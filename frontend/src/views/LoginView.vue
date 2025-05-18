<template>
  <div class="login-container">
    <el-row :gutter="20" justify="center">
      <el-col :xs="24" :sm="16" :md="12" :lg="8">
        <el-card class="login-card">
          <template #header>
            <div class="card-header">
              <h2>{{ isLogin ? '登录' : '注册' }}</h2>
            </div>
          </template>
          
          <!-- 登录表单 -->
          <el-form
            v-if="isLogin"
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入密码" 
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
                登录
              </el-button>
            </el-form-item>
            
            <div class="form-footer">
              <p>还没有账号？<a href="javascript:void(0)" @click="toggleForm">立即注册</a></p>
            </div>
          </el-form>
          
          <!-- 注册表单 -->
          <el-form
            v-else
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名" />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="registerForm.password" 
                type="password" 
                placeholder="请输入密码" 
                show-password
              />
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input 
                v-model="registerForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入密码" 
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
                注册
              </el-button>
            </el-form-item>
            
            <div class="form-footer">
              <p>已有账号？<a href="javascript:void(0)" @click="toggleForm">立即登录</a></p>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loading = ref(false)

// 控制显示登录还是注册表单
const isLogin = ref(true)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

// 监听路由参数，自动切换到注册模式
watch(
  () => route.query.mode,
  (mode) => {
    if (mode === 'register') {
      isLogin.value = false
    } else {
      isLogin.value = true
    }
  },
  { immediate: true }
)

// 切换登录/注册表单
const toggleForm = () => {
  isLogin.value = !isLogin.value
  // 切换时清除路由参数，避免模式混乱
  router.replace({ query: {} })
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const result = await userStore.login(loginForm)
        if (result.success) {
          ElMessage.success('登录成功')
          // 登录后跳转
          const redirectPath = route.query.redirect || '/'
          router.push(redirectPath)
        } else {
          ElMessage.error(result.message || '登录失败')
        }
      } catch (error) {
        ElMessage.error('登录过程中发生错误')
      } finally {
        loading.value = false
      }
    }
  })
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 移除确认密码字段
        const { confirmPassword, ...registerData } = registerForm
        const result = await userStore.register(registerData)
        if (result.success) {
          ElMessage.success('注册成功，请登录')
          isLogin.value = true
          loginForm.username = registerForm.username
          loginForm.password = ''
        } else {
          ElMessage.error(result.message || '注册失败')
        }
      } catch (error) {
        ElMessage.error('注册过程中发生错误')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.login-card {
  margin-top: 20px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #1E88E5;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
}

.form-footer a {
  color: #1E88E5;
  cursor: pointer;
}

.form-footer a:hover {
  text-decoration: underline;
}
</style>