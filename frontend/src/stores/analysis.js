import { defineStore } from 'pinia';
import { 
  getAnalysisByInterview, 
  analyzeQuickPractice 
} from '@/api/analysis';

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    // 分析结果数据
    analysisData: null,
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 当前分析类型
    analysisType: 'standard', // 'standard' 或 'quick_practice'
  }),
  
  getters: {
    // 获取分析结果
    getAnalysisResult() {
      return this.analysisData;
    },
    
    // 获取快速练习PLUS分析结果
    getQuickPracticeResult() {
      if (this.analysisData && this.analysisData.analysis_type === 'quick_practice') {
        return this.analysisData.quick_practice;
      }
      return null;
    },
    
    // 获取标准分析结果
    getStandardAnalysisResult() {
      if (this.analysisData && this.analysisData.analysis_type === 'standard') {
        return {
          speech: this.analysisData.speech,
          visual: this.analysisData.visual,
          content: this.analysisData.content,
          overall: this.analysisData.overall
        };
      }
      return null;
    },
    
    // 获取总体得分
    getOverallScore() {
      if (!this.analysisData) return 0;
      
      if (this.analysisData.analysis_type === 'quick_practice' && this.analysisData.quick_practice) {
        return this.analysisData.quick_practice.feedback.overall_score;
      }
      
      return this.analysisData.overall_score * 10; // 转换为百分制
    },
    
    // 是否有分析结果
    hasAnalysisResult() {
      return !!this.analysisData;
    },
    
    // 是否正在加载
    isLoading() {
      return this.loading;
    }
  },
  
  actions: {
    // 重置状态
    resetState() {
      this.analysisData = null;
      this.loading = false;
      this.error = null;
    },
    
    // 设置分析类型
    setAnalysisType(type) {
      this.analysisType = type;
    },
    
    // 获取面试的分析结果
    async fetchAnalysisByInterview(interviewId) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await getAnalysisByInterview(interviewId);
        this.analysisData = response.data;
        this.analysisType = response.data.analysis_type || 'standard';
        return response.data;
      } catch (error) {
        this.error = error.message || '获取分析结果失败';
        console.error('获取分析结果失败:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    // 提交快速练习回答进行分析
    async submitQuickPracticeAnalysis(data, audioFile = null) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await analyzeQuickPractice(data, audioFile);
        this.analysisData = response.data;
        this.analysisType = 'quick_practice';
        return response.data;
      } catch (error) {
        this.error = error.message || '快速练习分析失败';
        console.error('快速练习分析失败:', error);
        return null;
      } finally {
        this.loading = false;
      }
    }
  }
});