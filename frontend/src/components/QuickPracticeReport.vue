<template>
  <div class="quick-practice-report">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <h2>面试表现综合诊断报告</h2>
          <el-tag type="info">快速练习PLUS</el-tag>
        </div>
      </template>
      
      <!-- 总分和模块得分 -->
      <div class="score-section">
        <div class="overall-score">
          <h3>面试总分</h3>
          <div class="score-display">
            <span class="score-value">{{ Math.round(report.feedback.overall_score) }}</span>
            <span class="score-max">/100</span>
          </div>
        </div>
        
        <div class="module-scores">
          <div class="module-score">
            <div class="module-label">内容质量模块</div>
            <el-progress 
              :percentage="Math.round(report.feedback.content_quality_score)" 
              :color="getScoreColor(report.feedback.content_quality_score)"
              :stroke-width="15"
              :show-text="false"
            />
            <div class="score-text">{{ Math.round(report.feedback.content_quality_score) }}/100</div>
          </div>
          
          <div class="module-score">
            <div class="module-label">思维能力模块</div>
            <el-progress 
              :percentage="Math.round(report.feedback.cognitive_skills_score)" 
              :color="getScoreColor(report.feedback.cognitive_skills_score)"
              :stroke-width="15"
              :show-text="false"
            />
            <div class="score-text">{{ Math.round(report.feedback.cognitive_skills_score) }}/100</div>
          </div>
          
          <div class="module-score" v-if="report.communication_skills">
            <div class="module-label">沟通技巧模块</div>
            <el-progress 
              :percentage="Math.round(report.feedback.communication_skills_score)" 
              :color="getScoreColor(report.feedback.communication_skills_score)"
              :stroke-width="15"
              :show-text="false"
            />
            <div class="score-text">{{ Math.round(report.feedback.communication_skills_score) }}/100</div>
          </div>
        </div>
      </div>
      
      <!-- 能力雷达图 -->
      <div class="radar-chart-container">
        <canvas ref="radarChart"></canvas>
      </div>
      
      <el-divider />
      
      <!-- 亮点时刻 -->
      <div class="strengths-section">
        <h3>
          <el-icon><StarFilled /></el-icon>
          亮点时刻 (Strengths)
        </h3>
        <div class="strengths-list">
          <div v-for="(strength, index) in report.feedback.strengths" :key="`strength-${index}`" class="strength-item">
            <el-icon color="#67C23A"><Check /></el-icon>
            <div class="strength-content">
              <strong>亮点{{ index + 1 }}:</strong> {{ strength.description }}
            </div>
          </div>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 优先成长区 -->
      <div class="growth-areas-section">
        <h3>
          <el-icon><Opportunity /></el-icon>
          优先成长区 (Areas for Growth)
        </h3>
        <div class="growth-areas-list">
          <div v-for="(area, index) in report.feedback.growth_areas" :key="`area-${index}`" class="growth-area-item">
            <div class="growth-area-header">
              <el-icon color="#E6A23C"><Warning /></el-icon>
              <div class="growth-area-title">
                <strong>建议{{ index + 1 }}{{ index === 0 ? ' (最重要)' : '' }}:</strong>
                {{ getCategoryTitle(area.category, area.item) }}
              </div>
            </div>
            <div class="growth-area-details">
              <div class="diagnosis">
                <strong>现状诊断:</strong> {{ area.description }}
              </div>
              <div class="action-suggestion">
                <strong>行动建议:</strong> {{ area.action_suggestion }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 详细分析结果 (可折叠) -->
      <el-collapse class="detailed-analysis">
        <el-collapse-item title="查看详细分析数据" name="1">
          <div class="analysis-details">
            <h4>内容质量分析</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="回答相关性">{{ report.content_quality.relevance_review }}</el-descriptions-item>
              <el-descriptions-item label="细节与深度">{{ report.content_quality.depth_review }}</el-descriptions-item>
              <el-descriptions-item label="专业性">{{ report.content_quality.professional_style_review }}</el-descriptions-item>
              <el-descriptions-item label="匹配关键词">{{ report.content_quality.matched_keywords.join(', ') }}</el-descriptions-item>
            </el-descriptions>
            
            <h4>思维能力分析</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="逻辑结构">{{ report.cognitive_skills.structure_review }}</el-descriptions-item>
              <el-descriptions-item label="思维清晰度">{{ report.cognitive_skills.clarity_review }}</el-descriptions-item>
            </el-descriptions>
            
            <template v-if="report.communication_skills">
              <h4>沟通技巧分析</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="语言流畅度">
                  检测到{{ report.communication_skills.fluency_details.filler_words_count }}个填充词，
                  {{ report.communication_skills.fluency_details.unnatural_pauses_count }}次不自然停顿
                </el-descriptions-item>
                <el-descriptions-item label="语速">
                  {{ report.communication_skills.speech_rate_details.words_per_minute }}字/分钟，
                  语速{{ report.communication_skills.speech_rate_details.pace_category }}
                </el-descriptions-item>
                <el-descriptions-item label="声音能量">
                  {{ report.communication_skills.vocal_energy_details.pitch_category }}
                </el-descriptions-item>
                <el-descriptions-item label="语言简洁性">
                  {{ report.communication_skills.conciseness_review }}
                </el-descriptions-item>
              </el-descriptions>
            </template>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { StarFilled, Check, Warning, Opportunity } from '@element-plus/icons-vue';
import Chart from 'chart.js/auto';

const props = defineProps({
  analysisResult: {
    type: Object,
    required: true
  }
});

const report = computed(() => {
  return props.analysisResult.quick_practice || {
    content_quality: {},
    cognitive_skills: {},
    communication_skills: null,
    feedback: {
      strengths: [],
      growth_areas: [],
      content_quality_score: 0,
      cognitive_skills_score: 0,
      communication_skills_score: 0,
      overall_score: 0
    }
  };
});

const radarChart = ref(null);
let chartInstance = null;

// 获取分数对应的颜色
const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'; // 绿色 - 优秀
  if (score >= 70) return '#409EFF'; // 蓝色 - 良好
  if (score >= 60) return '#E6A23C'; // 橙色 - 中等
  return '#F56C6C'; // 红色 - 需要改进
};

// 获取类别标题
const getCategoryTitle = (category, item) => {
  const categories = {
    content_quality: {
      relevance: "提升回答相关性",
      depth_and_detail: "增加回答的细节与深度",
      professionalism: "提升专业性表达"
    },
    cognitive_skills: {
      logical_structure: "改善逻辑结构",
      clarity_of_thought: "提升思维清晰度"
    },
    communication_skills: {
      fluency: "优化语言流畅度",
      speech_rate: "调整语速",
      vocal_energy: "增强声音表现力",
      conciseness: "提高语言简洁性"
    }
  };
  
  return categories[category]?.[item] || `提升${item}`;
};

// 初始化雷达图
const initRadarChart = () => {
  if (!radarChart.value) return;
  
  const ctx = radarChart.value.getContext('2d');
  
  // 准备雷达图数据
  const labels = [];
  const data = [];
  
  // 内容质量维度
  if (report.value.content_quality) {
    labels.push('回答相关性');
    data.push(report.value.content_quality.relevance * 10);
    
    labels.push('细节与深度');
    data.push(report.value.content_quality.depth_and_detail * 10);
    
    labels.push('专业性');
    data.push(report.value.content_quality.professionalism * 10);
  }
  
  // 思维能力维度
  if (report.value.cognitive_skills) {
    labels.push('逻辑结构');
    data.push(report.value.cognitive_skills.logical_structure * 10);
    
    labels.push('思维清晰度');
    data.push(report.value.cognitive_skills.clarity_of_thought * 10);
  }
  
  // 沟通技巧维度
  if (report.value.communication_skills) {
    labels.push('语言流畅度');
    data.push(report.value.communication_skills.fluency * 10);
    
    labels.push('语速');
    data.push(report.value.communication_skills.speech_rate * 10);
    
    labels.push('声音能量');
    data.push(report.value.communication_skills.vocal_energy * 10);
    
    labels.push('语言简洁性');
    data.push(report.value.communication_skills.conciseness * 10);
  }
  
  // 销毁旧的图表实例
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  // 创建新的图表实例
  chartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: '能力评分',
        data: data,
        fill: true,
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgb(54, 162, 235)',
        pointBackgroundColor: 'rgb(54, 162, 235)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(54, 162, 235)'
      }]
    },
    options: {
      scales: {
        r: {
          angleLines: {
            display: true
          },
          suggestedMin: 0,
          suggestedMax: 100
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw}/100`;
            }
          }
        }
      }
    }
  });
};

// 监听分析结果变化，更新图表
watch(() => props.analysisResult, () => {
  // 在下一个渲染周期更新图表
  setTimeout(() => {
    initRadarChart();
  }, 0);
}, { deep: true });

onMounted(() => {
  // 初始化图表
  initRadarChart();
});
</script>

<style scoped>
.quick-practice-report {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.score-section {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
}

.overall-score {
  flex: 0 0 150px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 15px;
  border-radius: 8px;
  background-color: #f5f7fa;
}

.overall-score h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1rem;
  color: #606266;
}

.score-display {
  display: flex;
  align-items: baseline;
}

.score-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #409EFF;
}

.score-max {
  font-size: 1rem;
  color: #909399;
  margin-left: 2px;
}

.module-scores {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.module-score {
  display: flex;
  align-items: center;
  gap: 10px;
}

.module-label {
  flex: 0 0 120px;
  font-weight: bold;
  color: #606266;
}

.module-score .el-progress {
  flex: 1;
}

.score-text {
  flex: 0 0 60px;
  text-align: right;
  color: #606266;
}

.radar-chart-container {
  height: 300px;
  margin: 20px 0;
}

.strengths-section,
.growth-areas-section {
  margin: 20px 0;
}

.strengths-section h3,
.growth-areas-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.2rem;
  margin-bottom: 15px;
}

.strengths-list,
.growth-areas-list {
  padding-left: 10px;
}

.strength-item,
.growth-area-item {
  margin-bottom: 15px;
}

.strength-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #67C23A;
}

.strength-content {
  color: #303133;
}

.growth-area-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #E6A23C;
  margin-bottom: 5px;
}

.growth-area-title {
  color: #303133;
}

.growth-area-details {
  margin-left: 24px;
  padding: 8px;
  background-color: #fdf6ec;
  border-left: 3px solid #E6A23C;
  border-radius: 0 4px 4px 0;
}

.diagnosis,
.action-suggestion {
  margin-bottom: 5px;
}

.detailed-analysis {
  margin-top: 20px;
}

.analysis-details h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #606266;
}

.analysis-details .el-descriptions {
  margin-bottom: 20px;
}
</style>