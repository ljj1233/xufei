<template>
  <div class="emotion-icon">
    <div v-if="type === 'excellent'" class="icon excellent">
      <span class="emoji">😊</span>
      <span class="text" v-if="showText">优秀</span>
    </div>
    <div v-else-if="type === 'good'" class="icon good">
      <span class="emoji">🙂</span>
      <span class="text" v-if="showText">良好</span>
    </div>
    <div v-else-if="type === 'average'" class="icon average">
      <span class="emoji">😐</span>
      <span class="text" v-if="showText">一般</span>
    </div>
    <div v-else-if="type === 'needsImprovement'" class="icon needs-improvement">
      <span class="emoji">🤔</span>
      <span class="text" v-if="showText">需改进</span>
    </div>
    <div v-else-if="type === 'loading'" class="icon loading">
      <span class="emoji">⏳</span>
      <span class="text" v-if="showText">分析中</span>
    </div>
    <div v-else-if="type === 'tip'" class="icon tip">
      <span class="emoji">💡</span>
      <span class="text" v-if="showText">小贴士</span>
    </div>
    <div v-else-if="type === 'success'" class="icon success">
      <span class="emoji">🎉</span>
      <span class="text" v-if="showText">成功</span>
    </div>
    <div v-else class="icon default">
      <span class="emoji">😊</span>
      <span class="text" v-if="showText">{{type}}</span>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  type: {
    type: String,
    default: 'good'
  },
  showText: {
    type: Boolean,
    default: true
  }
})
</script>

<style scoped>
.emotion-icon {
  display: inline-flex;
  align-items: center;
}

.icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.emoji {
  font-size: 24px;
  line-height: 1;
}

.text {
  font-size: 12px;
  margin-top: 4px;
}

.excellent .emoji {
  color: #67C23A;
}

.good .emoji {
  color: #409EFF;
}

.average .emoji {
  color: #E6A23C;
}

.needs-improvement .emoji {
  color: #F56C6C;
}

.loading .emoji {
  animation: spin 2s linear infinite;
}

.tip .emoji {
  color: #909399;
}

.success .emoji {
  animation: bounce 0.5s ease-in-out;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
</style> 