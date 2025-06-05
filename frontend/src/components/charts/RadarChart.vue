<template>
  <div class="radar-chart-wrapper">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

// 注册Chart.js组件
Chart.register(...registerables)

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const canvas = ref(null)
let chartInstance = null

const createChart = () => {
  if (!canvas.value) return
  
  const ctx = canvas.value.getContext('2d')
  
  // 销毁旧的实例
  if (chartInstance) {
    chartInstance.destroy()
  }
  
  // 默认配置
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          display: true
        },
        beginAtZero: true,
        suggestedMin: 0,
        suggestedMax: 10,
        ticks: {
          stepSize: 2
        }
      }
    },
    plugins: {
      legend: {
        position: 'top'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.raw}/10`
          }
        }
      }
    }
  }
  
  // 合并配置
  const mergedOptions = {
    ...defaultOptions,
    ...props.options
  }
  
  // 创建图表
  chartInstance = new Chart(ctx, {
    type: 'radar',
    data: props.chartData,
    options: mergedOptions
  })
}

// 监听数据变化
watch(() => props.chartData, () => {
  nextTick(() => createChart())
}, { deep: true })

// 监听配置变化
watch(() => props.options, () => {
  nextTick(() => createChart())
}, { deep: true })

// 销毁图表
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

onMounted(() => {
  createChart()
})
</script>

<style scoped>
.radar-chart-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}
</style> 