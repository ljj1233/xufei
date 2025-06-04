<template>
  <div class="admin-container">
    <el-card class="admin-card">
      <template #header>
        <div class="card-header">
          <h2>管理员控制台</h2>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else>
        <el-tabs type="border-card">
          <el-tab-pane label="用户管理">
            <div class="search-bar">
              <el-input
                v-model="searchQuery"
                placeholder="搜索用户名或邮箱"
                prefix-icon="el-icon-search"
                clearable
                @input="filterUsers"
                style="width: 300px;"
              />
            </div>
            
            <el-table :data="filteredUsers" style="width: 100%" border>
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="username" label="用户名" width="150" />
              <el-table-column prop="email" label="邮箱" width="180" />
              <el-table-column prop="created_at" label="注册时间" width="180">
                <template #default="scope">
                  {{ formatDate(scope.row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                    {{ scope.row.is_active ? '正常' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_admin" label="角色" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_admin ? 'warning' : 'info'">
                    {{ scope.row.is_admin ? '管理员' : '普通用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button
                    size="small"
                    :type="scope.row.is_active ? 'danger' : 'success'"
                    @click="updateUserStatus(scope.row)"
                    :disabled="scope.row.id === currentUser.id"
                  >
                    {{ scope.row.is_active ? '停用' : '启用' }}
                  </el-button>
                  <el-button
                    size="small"
                    :type="scope.row.is_admin ? 'info' : 'warning'"
                    @click="updateUserAdmin(scope.row)"
                    :disabled="scope.row.id === currentUser.id"
                  >
                    {{ scope.row.is_admin ? '取消管理员' : '设为管理员' }}
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteUser(scope.row)"
                    :disabled="scope.row.id === currentUser.id"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <div class="pagination-container">
              <el-pagination
                layout="prev, pager, next"
                :total="totalUsers"
                :page-size="pageSize"
                @current-change="fetchUsers"
              />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="系统概览">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card class="statistic-card">
                  <div class="statistic-title">总用户数</div>
                  <div class="statistic-value">{{ systemStats.userCount }}</div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="statistic-card">
                  <div class="statistic-title">总面试数</div>
                  <div class="statistic-value">{{ systemStats.interviewCount }}</div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="statistic-card">
                  <div class="statistic-title">今日新增用户</div>
                  <div class="statistic-value">{{ systemStats.todayNewUsers }}</div>
                </el-card>
              </el-col>
            </el-row>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
    
    <!-- 确认对话框 -->
    <el-dialog v-model="confirmDialogVisible" :title="confirmDialogTitle" width="400px">
      <span>{{ confirmDialogMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="confirmDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDialogAction" :loading="actionLoading">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(true)
const actionLoading = ref(false)
const users = ref([])
const filteredUsers = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalUsers = ref(0)
const currentUser = ref({})

// 系统统计
const systemStats = reactive({
  userCount: 0,
  interviewCount: 0,
  todayNewUsers: 0
})

// 确认对话框
const confirmDialogVisible = ref(false)
const confirmDialogTitle = ref('')
const confirmDialogMessage = ref('')
const confirmDialogAction = ref(() => {})

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

// 获取用户列表
const fetchUsers = async (page = 1) => {
  loading.value = true
  currentPage.value = page
  try {
    const result = await userStore.getUsers(page, pageSize.value)
    if (result.success) {
      users.value = result.data.items
      filteredUsers.value = users.value
      totalUsers.value = result.data.total
      
      // 获取当前用户信息
      const userInfo = await userStore.getUserInfo()
      if (userInfo.success) {
        currentUser.value = userInfo.data
      }
    } else {
      ElMessage.error(result.message || '获取用户列表失败')
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取系统统计信息
const fetchSystemStats = async () => {
  try {
    // 这里应该调用获取系统统计的API
    // 由于没有实现，暂时使用模拟数据
    systemStats.userCount = users.value.length
    systemStats.interviewCount = 0
    systemStats.todayNewUsers = 0
  } catch (error) {
    console.error('获取系统统计失败:', error)
  }
}

// 筛选用户
const filterUsers = () => {
  if (!searchQuery.value) {
    filteredUsers.value = users.value
    return
  }
  
  const query = searchQuery.value.toLowerCase()
  filteredUsers.value = users.value.filter(user => 
    user.username.toLowerCase().includes(query) || 
    user.email.toLowerCase().includes(query)
  )
}

// 更新用户状态
const updateUserStatus = (user) => {
  confirmDialogTitle.value = user.is_active ? '停用用户' : '启用用户'
  confirmDialogMessage.value = `确定要${user.is_active ? '停用' : '启用'}用户 "${user.username}" 吗？`
  
  confirmDialogAction.value = async () => {
    actionLoading.value = true
    try {
      const result = await userStore.updateUserStatus(user.id, !user.is_active)
      if (result.success) {
        ElMessage.success(`${user.is_active ? '停用' : '启用'}用户成功`)
        user.is_active = !user.is_active
      } else {
        ElMessage.error(result.message || `${user.is_active ? '停用' : '启用'}用户失败`)
      }
    } catch (error) {
      console.error('更新用户状态失败:', error)
      ElMessage.error('操作失败，请稍后重试')
    } finally {
      actionLoading.value = false
      confirmDialogVisible.value = false
    }
  }
  
  confirmDialogVisible.value = true
}

// 更新用户管理员权限
const updateUserAdmin = (user) => {
  confirmDialogTitle.value = user.is_admin ? '取消管理员权限' : '授予管理员权限'
  confirmDialogMessage.value = `确定要${user.is_admin ? '取消' : '授予'}用户 "${user.username}" 的管理员权限吗？`
  
  confirmDialogAction.value = async () => {
    actionLoading.value = true
    try {
      const result = await userStore.updateUserAdmin(user.id, !user.is_admin)
      if (result.success) {
        ElMessage.success(`${user.is_admin ? '取消' : '授予'}管理员权限成功`)
        user.is_admin = !user.is_admin
      } else {
        ElMessage.error(result.message || `${user.is_admin ? '取消' : '授予'}管理员权限失败`)
      }
    } catch (error) {
      console.error('更新管理员权限失败:', error)
      ElMessage.error('操作失败，请稍后重试')
    } finally {
      actionLoading.value = false
      confirmDialogVisible.value = false
    }
  }
  
  confirmDialogVisible.value = true
}

// 删除用户
const deleteUser = (user) => {
  confirmDialogTitle.value = '删除用户'
  confirmDialogMessage.value = `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`
  
  confirmDialogAction.value = async () => {
    actionLoading.value = true
    try {
      const result = await userStore.deleteUserById(user.id)
      if (result.success) {
        ElMessage.success('删除用户成功')
        // 从列表中移除
        users.value = users.value.filter(u => u.id !== user.id)
        filteredUsers.value = filteredUsers.value.filter(u => u.id !== user.id)
      } else {
        ElMessage.error(result.message || '删除用户失败')
      }
    } catch (error) {
      console.error('删除用户失败:', error)
      ElMessage.error('操作失败，请稍后重试')
    } finally {
      actionLoading.value = false
      confirmDialogVisible.value = false
    }
  }
  
  confirmDialogVisible.value = true
}

// 页面加载时获取数据
onMounted(() => {
  fetchUsers()
  fetchSystemStats()
})
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 20px auto;
}

.admin-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container {
  padding: 20px;
  text-align: center;
}

.search-bar {
  margin-bottom: 15px;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}

.statistic-card {
  text-align: center;
  padding: 15px;
}

.statistic-title {
  font-size: 16px;
  color: #606266;
  margin-bottom: 10px;
}

.statistic-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}
</style> 