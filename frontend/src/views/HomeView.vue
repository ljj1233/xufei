<template>
  <div class="home-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="hero-section">
          <div class="hero-content">
            <h1>多模态面试评测智能体</h1>
            <p class="subtitle">基于AI技术的面试视频/音频分析系统，提供专业评估和改进建议</p>
            <div class="emotion-container">
              <div class="emotion-item">
                <EmotionIcons type="excellent" />
                <span>提升表现</span>
              </div>
              <div class="emotion-item">
                <EmotionIcons type="good" />
                <span>专业分析</span>
              </div>
              <div class="emotion-item">
                <EmotionIcons type="tip" />
                <span>实用建议</span>
              </div>
            </div>
            <div class="hero-actions">
              <template v-if="!userStore.isLoggedIn">
                <el-button type="primary" size="large" @click="router.push('/login')">立即登录</el-button>
                <el-button size="large" @click="router.push('/register')">注册账号</el-button>
                <el-button type="info" plain size="large" @click="router.push('/about')">关于我们</el-button>
              </template>
              <template v-else>
                <el-button type="primary" size="large" @click="router.push('/upload')">上传面试</el-button>
                <el-button size="large" @click="router.push('/results')">查看分析结果</el-button>
                <el-button size="large" @click="router.push('/user')">个人中心</el-button>
              </template>
            </div>
          </div>
          <div class="hero-image">
            <img src="../assets/images/interview-hero.svg" alt="面试场景插图" />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <div class="motivation-section">
      <div class="quote-box">
        <i class="quote-mark">"</i>
        <p class="quote-text">准备好展示最好的自己了吗？每次练习都是进步的机会！</p>
      </div>
    </div>
    
    <el-row :gutter="20" class="features-section">
      <el-col :span="24">
        <h2 class="section-title">主要功能</h2>
        <p class="section-subtitle">全方位分析，助您成为面试达人</p>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon><VideoCamera /></el-icon>
              <h3>多模态分析</h3>
            </div>
          </template>
          <p>支持视频和音频分析，从语音、视觉和内容三个维度全方位评估面试表现</p>
          <div class="feature-tags">
            <el-tag size="small">视频分析</el-tag>
            <el-tag size="small">音频分析</el-tag>
            <el-tag size="small">多维度评估</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon><DataAnalysis /></el-icon>
              <h3>AI驱动评估</h3>
            </div>
          </template>
          <p>利用先进的AI技术进行语音识别、情感分析和专业知识评估</p>
          <div class="feature-tags">
            <el-tag size="small">语音识别</el-tag>
            <el-tag size="small">情感分析</el-tag>
            <el-tag size="small">专业评估</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="feature-header">
              <el-icon><Document /></el-icon>
              <h3>详细报告</h3>
            </div>
          </template>
          <p>生成量化评分和具体改进建议，帮助用户提升面试表现</p>
          <div class="feature-tags">
            <el-tag size="small">能力雷达图</el-tag>
            <el-tag size="small">量化评分</el-tag>
            <el-tag size="small">个性化建议</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="how-it-works-section">
      <el-col :span="24">
        <h2 class="section-title">使用流程</h2>
        <p class="section-subtitle">三步轻松获取专业面试评估</p>
      </el-col>
      <el-col :span="24">
        <div class="steps-container">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-icon">
              <el-icon><Upload /></el-icon>
            </div>
            <h4>上传面试</h4>
            <p>上传您的面试视频或音频文件</p>
          </div>
          <div class="step-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-icon">
              <el-icon><Loading /></el-icon>
            </div>
            <h4>AI分析</h4>
            <p>系统对您的面试进行多维度分析</p>
          </div>
          <div class="step-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-icon">
              <el-icon><DocumentChecked /></el-icon>
            </div>
            <h4>查看报告</h4>
            <p>获取详细评估报告和改进建议</p>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="scenarios-section">
      <el-col :span="24">
        <h2 class="section-title">适用场景</h2>
        <p class="section-subtitle">为各类岗位面试提供专业评估</p>
      </el-col>
      <el-col :span="24">
        <el-card shadow="hover">
          <el-tabs>
            <el-tab-pane label="技术岗">
              <div class="tab-content">
                <div class="tab-text">
                  <h4>技术岗位面试评估</h4>
                  <p>适用于软件工程师、数据科学家、AI工程师等技术岗位的面试评估</p>
                  <div class="tag-group">
                    <el-tag>人工智能</el-tag>
                    <el-tag>大数据</el-tag>
                    <el-tag>物联网</el-tag>
                    <el-tag>智能系统</el-tag>
                  </div>
                </div>
                <div class="tab-image">
                  <EmotionIcons type="good" />
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="产品岗">
              <div class="tab-content">
                <div class="tab-text">
                  <h4>产品岗位面试评估</h4>
                  <p>适用于产品经理、产品运营等产品岗位的面试评估</p>
                  <div class="tag-group">
                    <el-tag>产品设计</el-tag>
                    <el-tag>用户体验</el-tag>
                    <el-tag>市场分析</el-tag>
                  </div>
                </div>
                <div class="tab-image">
                  <EmotionIcons type="excellent" />
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="运维测试岗">
              <div class="tab-content">
                <div class="tab-text">
                  <h4>运维测试岗位面试评估</h4>
                  <p>适用于运维工程师、测试工程师等岗位的面试评估</p>
                  <div class="tag-group">
                    <el-tag>系统运维</el-tag>
                    <el-tag>自动化测试</el-tag>
                    <el-tag>质量保证</el-tag>
                  </div>
                </div>
                <div class="tab-image">
                  <EmotionIcons type="good" />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="cta-section">
      <el-col :span="24">
        <el-card class="cta-card" shadow="hover">
          <h3>准备好提升你的面试表现了吗？</h3>
          <p>立即开始使用我们的AI面试评测系统，获取专业分析和改进建议</p>
          <div class="cta-actions">
            <el-button type="primary" size="large" @click="userStore.isLoggedIn ? router.push('/upload') : router.push('/login')">
              {{ userStore.isLoggedIn ? '立即上传面试' : '立即开始' }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { VideoCamera, DataAnalysis, Document, Upload, Loading, DocumentChecked, ArrowRight } from '@element-plus/icons-vue'
import EmotionIcons from '../components/EmotionIcons.vue'

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
  display: flex;
  align-items: center;
  padding: 60px 20px;
  background-color: #f0f8ff;
  border-radius: 12px;
  margin-bottom: 40px;
  position: relative;
  overflow: hidden;
}

.hero-content {
  flex: 1;
  z-index: 2;
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1;
}

.hero-image img {
  max-width: 100%;
  height: auto;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.hero-section h1 {
  font-size: 2.5rem;
  color: #1E88E5;
  margin-bottom: 20px;
  animation: fadeIn 1s ease-out;
}

.subtitle {
  font-size: 1.2rem;
  color: #606266;
  margin-bottom: 30px;
  max-width: 800px;
  animation: fadeIn 1s ease-out 0.3s both;
}

.emotion-container {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  animation: fadeIn 1s ease-out 0.6s both;
}

.emotion-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.emotion-item span {
  font-size: 14px;
  color: #606266;
}

.hero-actions {
  display: flex;
  gap: 20px;
  animation: fadeIn 1s ease-out 0.9s both;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.motivation-section {
  margin-bottom: 40px;
  text-align: center;
}

.quote-box {
  background-color: #ecf5ff;
  padding: 30px;
  border-radius: 8px;
  position: relative;
  max-width: 800px;
  margin: 0 auto;
}

.quote-mark {
  font-size: 60px;
  position: absolute;
  top: 10px;
  left: 20px;
  color: rgba(64, 158, 255, 0.2);
  font-family: serif;
}

.quote-text {
  font-size: 1.3rem;
  font-style: italic;
  color: #409EFF;
  position: relative;
  z-index: 1;
}

.section-title {
  text-align: center;
  margin-bottom: 10px;
  color: #303133;
  font-size: 1.8rem;
}

.section-subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 30px;
}

.features-section,
.scenarios-section,
.how-it-works-section,
.cta-section {
  margin-bottom: 60px;
}

.feature-card {
  height: 100%;
  margin-bottom: 20px;
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
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

.feature-tags {
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.steps-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  padding: 20px 0;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 200px;
  position: relative;
}

.step-number {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 30px;
  height: 30px;
  background-color: #1E88E5;
  color: white;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
}

.step-icon {
  width: 80px;
  height: 80px;
  background-color: #ecf5ff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 15px;
}

.step-icon .el-icon {
  font-size: 2.5rem;
}

.step-arrow {
  font-size: 2rem;
  color: #dcdfe6;
}

.step-item h4 {
  margin: 0 0 10px;
  color: #303133;
}

.step-item p {
  color: #606266;
  margin: 0;
}

.tab-content {
  display: flex;
  align-items: center;
}

.tab-text {
  flex: 3;
}

.tab-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.tab-text h4 {
  margin-top: 0;
  color: #303133;
}

.tag-group {
  margin-top: 15px;
}

.tag-group .el-tag {
  margin-right: 10px;
  margin-bottom: 10px;
}

.cta-card {
  text-align: center;
  padding: 40px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e1f5fe 100%);
}

.cta-card h3 {
  font-size: 1.8rem;
  color: #1E88E5;
  margin-top: 0;
}

.cta-actions {
  margin-top: 30px;
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    padding: 40px 10px;
  }
  
  .hero-section h1 {
    font-size: 2rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-image {
    margin-top: 30px;
  }
  
  .steps-container {
    flex-direction: column;
    gap: 30px;
  }
  
  .step-arrow {
    transform: rotate(90deg);
    margin: 10px 0;
  }
}
</style>