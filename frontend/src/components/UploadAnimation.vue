<!--
创建一个动态SVG动画组件，用于上传面试页面
包含三个动画：上传动画、分析动画和完成动画
-->

<template>
  <div class="upload-animation">
    <div v-if="type === 'upload'" class="upload-svg">
      <svg width="150" height="150" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="90" fill="none" stroke="#edf2f7" stroke-width="10" />
        <path 
          d="M100 40 L100 120 M70 70 L100 40 L130 70" 
          fill="none" 
          stroke="#003366" 
          stroke-width="10" 
          stroke-linecap="round"
          stroke-linejoin="round" 
        />
        <circle 
          cx="100" 
          cy="160" 
          r="10" 
          fill="#003366" 
          class="pulse-circle"
        />
        <path 
          d="M40 110 C40 150, 160 150, 160 110" 
          fill="none" 
          stroke="#1890ff" 
          stroke-width="6" 
          stroke-linecap="round"
          stroke-dasharray="320" 
          stroke-dashoffset="320" 
          class="progress-path"
        />
      </svg>
    </div>
    
    <div v-else-if="type === 'analysis'" class="analysis-svg">
      <svg width="150" height="150" viewBox="0 0 200 200">
        <rect x="40" y="60" width="120" height="90" rx="10" fill="#edf2f7" stroke="#003366" stroke-width="4" />
        <circle cx="100" cy="100" r="30" fill="#1890ff" opacity="0.6" class="analysis-circle" />
        <path 
          d="M80 60 L80 150 M120 60 L120 150 M40 105 L160 105" 
          stroke="#003366" 
          stroke-width="2" 
          stroke-dasharray="5,5"
        />
        <g class="data-points">
          <circle cx="60" cy="90" r="4" fill="#003366" />
          <circle cx="100" cy="75" r="4" fill="#003366" />
          <circle cx="140" cy="85" r="4" fill="#003366" />
          <circle cx="60" cy="120" r="4" fill="#003366" />
          <circle cx="100" cy="140" r="4" fill="#003366" />
          <circle cx="140" cy="125" r="4" fill="#003366" />
        </g>
        <path 
          d="M60 90 L100 75 L140 85 M60 120 L100 140 L140 125" 
          fill="none" 
          stroke="#003366" 
          stroke-width="2"
          stroke-dasharray="200" 
          stroke-dashoffset="0" 
          class="analysis-paths"
        />
      </svg>
    </div>
    
    <div v-else-if="type === 'complete'" class="complete-svg">
      <svg width="150" height="150" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="90" fill="#edf2f7" />
        <circle 
          cx="100" 
          cy="100" 
          r="70" 
          fill="none" 
          stroke="#1890ff" 
          stroke-width="12" 
          stroke-dasharray="440" 
          stroke-dashoffset="440" 
          class="complete-circle"
        />
        <path 
          d="M70 100 L90 125 L135 75" 
          fill="none" 
          stroke="#003366" 
          stroke-width="12" 
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-dasharray="130" 
          stroke-dashoffset="130" 
          class="check-mark"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'upload', // upload, analysis, complete
    validator: (value) => ['upload', 'analysis', 'complete'].includes(value)
  }
})
</script>

<style scoped>
.upload-animation {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px 0;
}

/* 上传动画 */
.upload-svg .pulse-circle {
  animation: pulse 2s infinite;
}

.upload-svg .progress-path {
  animation: progress 3s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes progress {
  0% {
    stroke-dashoffset: 320;
  }
  50% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 320;
  }
}

/* 分析动画 */
.analysis-svg .analysis-circle {
  animation: moveAround 4s infinite linear;
}

.analysis-svg .analysis-paths {
  animation: drawPaths 4s infinite;
}

.analysis-svg .data-points circle {
  animation: blink 2s infinite alternate;
}

@keyframes moveAround {
  0% {
    transform: translate(0, 0);
  }
  25% {
    transform: translate(30px, -10px);
  }
  50% {
    transform: translate(0, 20px);
  }
  75% {
    transform: translate(-30px, -10px);
  }
  100% {
    transform: translate(0, 0);
  }
}

@keyframes drawPaths {
  0% {
    stroke-dashoffset: 200;
  }
  50% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 200;
  }
}

@keyframes blink {
  from {
    opacity: 1;
  }
  to {
    opacity: 0.3;
  }
}

/* 完成动画 */
.complete-svg .complete-circle {
  animation: drawCircle 1.5s forwards ease-out;
}

.complete-svg .check-mark {
  animation: drawCheck 1s 0.8s forwards ease-out;
}

@keyframes drawCircle {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes drawCheck {
  to {
    stroke-dashoffset: 0;
  }
}
</style> 