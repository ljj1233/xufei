<template>
  <div class="home-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="hero-section">
          <h1>多模态面试评测智能体</h1>
          <p>基于AI技术的面试视频/音频分析系统，提供专业评估和改进建议</p>
          <div class="hero-actions" v-if="!userStore.isLoggedIn">
            <el-button type="primary" size="large" @click="router.push('/login')">立即登录</el-button>
            <el-button size="large" @click="router.push('/register')">注册账号</el-button>
          </div>
          <div class="hero-actions" v-else>
            <el-button type="primary" size="large" @click="router.push('/upload')">上传面试</el-button>
            <el-button size="large" @click="router.push('/results')">查看分析结果</el-button>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="features-section">
      <el-col :span="24">
        <h2 class="section-title">主要功能</h2>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon><VideoCamera /></el-icon>
              <h3>多模态分析</h3>
            </div>
          </template>
          <p>支持视频和音频分析，从语音、视觉和内容三个维度全方位评估面试表现</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon><DataAnalysis /></el-icon>
              <h3>AI驱动评估</h3>
            </div>
          </template>
          <p>利用先进的AI技术进行语音识别、情感分析和专业知识评估</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon><Document /></el-icon>
              <h3>详细报告</h3>
            </div>
          </template>
          <p>生成量化评分和具体改进建议，帮助用户提升面试表现</p>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="scenarios-section">
      <el-col :span="24">
        <h2 class="section-title">适用场景</h2>
      </el-col>
      <el-col :span="24">
        <el-card>
          <el-tabs>
            <el-tab-pane label="技术岗">
              <p>适用于软件工程师、数据科学家、AI工程师等技术岗位的面试评估</p>
              <el-tag>人工智能</el-tag>
              <el-tag>大数据</el-tag>
              <el-tag>物联网</el-tag>
              <el-tag>智能系统</el-tag>
            </el-tab-pane>
            <el-tab-pane label="产品岗">
              <p>适用于产品经理、产品运营等产品岗位的面试评估</p>
              <el-tag>产品设计</el-tag>
              <el-tag>用户体验</el-tag>
              <el-tag>市场分析</el-tag>
            </el-tab-pane>
            <el-tab-pane label="运维测试岗">
              <p>适用于运维工程师、测试工程师等岗位的面试评估</p>
              <el-tag>系统运维</el-tag>
              <el-tag>自动化测试</el-tag>
              <el-tag>质量保证</el-tag>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { VideoCamera, DataAnalysis, Document } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.hero-section {
  text-align: center;
  padding: 60px 20px;
  background-color: #f0f8ff;
  border-radius: 8px;
  margin-bottom: 40px;
}

.hero-section h1 {
  font-size: 2.5rem;
  color: #1E88E5;
  margin-bottom: 20px;
}

.hero-section p {
  font-size: 1.2rem;
  color: #606266;
  margin-bottom: 30px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.section-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
  font-size: 1.8rem;
}

.features-section,
.scenarios-section {
  margin-bottom: 40px;
}

.feature-card {
  height: 100%;
  margin-bottom: 20px;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.feature-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.el-icon {
  font-size: 1.5rem;
  color: #1E88E5;
}

.el-tag {
  margin-right: 10px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 40px 10px;
  }
  
  .hero-section h1 {
    font-size: 2rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>