<template>
  <div class="user-container">
    <h1 class="page-title">个人中心</h1>
    
    <el-row :gutter="24">
      <el-col :md="8" :sm="24">
        <el-card class="user-card">
          <template #header>
            <div class="card-header">
              <h3>个人信息</h3>
              <div class="action-buttons">
                <el-button type="primary" link @click="showEditDialog">
                  <el-icon><Edit /></el-icon>编辑资料
                </el-button>
              </div>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>
          
          <div v-else class="user-info">
            <div class="user-avatar">
              <el-avatar :size="80" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
            </div>
            <div class="user-details">
              <div class="user-name">{{ userInfo.username }}</div>
              <div class="user-email">{{ userInfo.email || '未设置邮箱' }}</div>
              <div class="user-since">注册时间：{{ formatDate(userInfo.created_at) }}</div>
            </div>
            
            <div class="user-actions">
              <el-button type="warning" plain size="small" @click="showPasswordDialog">
                <el-icon><Lock /></el-icon>修改密码
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :md="16" :sm="24">
        <!-- 面试统计组件 -->
        <interview-statistics />
      </el-col>
    </el-row>
    
    <!-- 修改信息对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑个人资料" width="500px" destroy-on-close>
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateUserInfo" :loading="updating">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="500px" destroy-on-close>
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" placeholder="请输入当前密码"></el-input>
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码"></el-input>
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请再次输入新密码"></el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updatePassword" :loading="updating">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userAPI } from '../api/user'
import InterviewStatistics from '../components/statistics/InterviewStatistics.vue'

const userInfo = ref({})
const loading = ref(true)
const updating = ref(false)

// 对话框控制
const editDialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const editFormRef = ref(null)
const passwordFormRef = ref(null)

// 编辑表单
const editForm = reactive({
  username: '',
  email: ''
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const editRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 密码验证规则
const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取用户信息
const fetchUserInfo = async () => {
  loading.value = true
  try {
    const result = await userAPI.getMe()
    userInfo.value = result
    // 填充编辑表单
    editForm.username = result.username
    editForm.email = result.email
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 显示编辑对话框
const showEditDialog = () => {
  editForm.username = userInfo.value.username
  editForm.email = userInfo.value.email
  editDialogVisible.value = true
}

// 显示密码对话框
const showPasswordDialog = () => {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordDialogVisible.value = true
}

// 更新用户信息
const updateUserInfo = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        const result = await userAPI.updateProfile({
          username: editForm.username,
          email: editForm.email
        })
        
        userInfo.value = result
        ElMessage.success('个人信息更新成功')
        editDialogVisible.value = false
      } catch (error) {
        console.error('更新用户信息失败:', error)
        ElMessage.error(error.response?.data?.message || '更新失败，请稍后重试')
      } finally {
        updating.value = false
      }
    }
  })
}

// 更新密码
const updatePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        await userAPI.changePassword({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        })
        
        ElMessage.success('密码修改成功')
        passwordDialogVisible.value = false
      } catch (error) {
        console.error('修改密码失败:', error)
        ElMessage.error(error.response?.data?.message || '修改失败，请稍后重试')
      } finally {
        updating.value = false
      }
    }
  })
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.user-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 500;
  color: var(--text-primary);
  position: relative;
  padding-left: 16px;
}

.page-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10%;
  width: 4px;
  height: 80%;
  background-color: var(--primary-color);
  border-radius: 2px;
}

.user-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.loading-container {
  padding: 20px 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.user-avatar {
  margin-bottom: 16px;
}

.user-details {
  text-align: center;
  margin-bottom: 20px;
  width: 100%;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.user-email {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.user-since {
  font-size: 12px;
  color: var(--text-disabled);
}

.user-actions {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

@media (max-width: 768px) {
  .el-row {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
}
</style>