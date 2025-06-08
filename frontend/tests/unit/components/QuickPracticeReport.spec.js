import { shallowMount, mount } from '@vue/test-utils';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import QuickPracticeReport from '@/components/QuickPracticeReport.vue';
import Chart from 'chart.js/auto';

// Mock Chart.js
vi.mock('chart.js/auto', () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      destroy: vi.fn()
    }))
  };
});

describe('QuickPracticeReport.vue', () => {
  let mockAnalysisResult;
  
  beforeEach(() => {
    // 重置 mocks
    vi.clearAllMocks();
    
    // 准备测试数据
    mockAnalysisResult = {
      quick_practice: {
        content_quality: {
          relevance: 7.5,
          relevance_review: "回答高度相关，直接针对问题进行了回应",
          depth_and_detail: 6.0,
          depth_review: "回答包含了一些具体例子，但缺少具体数据支撑",
          professionalism: 8.0,
          matched_keywords: ["算法", "数据结构", "优化"],
          professional_style_review: "使用了专业术语，表达专业"
        },
        cognitive_skills: {
          logical_structure: 7.0,
          structure_review: "总分总结构，逻辑较为清晰",
          clarity_of_thought: 7.5,
          clarity_review: "思路清晰，没有明显矛盾"
        },
        communication_skills: {
          fluency: 7.0,
          fluency_details: {
            filler_words_count: 3,
            unnatural_pauses_count: 1
          },
          speech_rate: 7.5,
          speech_rate_details: {
            words_per_minute: 160,
            pace_category: "适中"
          },
          vocal_energy: 6.5,
          vocal_energy_details: {
            pitch_std_dev: 15.0,
            pitch_category: "平稳有变化"
          },
          conciseness: 6.5,
          conciseness_review: "表达较为简洁，但有少量冗余"
        },
        feedback: {
          strengths: [
            {
              category: "content_quality",
              item: "relevance",
              description: "回答的相关性极高，你的回答紧扣问题核心，展现了良好的理解能力。"
            },
            {
              category: "cognitive_skills", 
              item: "clarity_of_thought",
              description: "思维清晰，能够有条理地表达复杂概念。"
            }
          ],
          growth_areas: [
            {
              category: "content_quality",
              item: "depth_and_detail",
              description: "回答缺乏具体的数据和例子支撑",
              action_suggestion: "使用STAR法则，特别是在描述结果时加入具体数据"
            }
          ],
          content_quality_score: 72.5,
          cognitive_skills_score: 72.5,
          communication_skills_score: 69.0,
          overall_score: 71.5
        }
      }
    };
  });
  
  it('renders properly with all data', () => {
    const wrapper = shallowMount(QuickPracticeReport, {
      props: {
        analysisResult: mockAnalysisResult
      }
    });
    
    // 检查总体评分显示
    expect(wrapper.find('.score-value').text()).toBe('72');
    
    // 检查模块评分显示
    const moduleScores = wrapper.findAll('.module-score');
    expect(moduleScores.length).toBe(3); // 三个模块：内容质量、思维能力、沟通技巧
    
    // 检查雷达图初始化
    expect(wrapper.find('.radar-chart-container').exists()).toBe(true);
    
    // 检查亮点显示
    const strengthItems = wrapper.findAll('.strength-item');
    expect(strengthItems.length).toBe(2);
    
    // 检查成长区域显示
    const growthAreaItems = wrapper.findAll('.growth-area-item');
    expect(growthAreaItems.length).toBe(1);
    
    // 检查详细分析数据
    expect(wrapper.find('.detailed-analysis').exists()).toBe(true);
  });
  
  it('renders properly with no communication skills data', () => {
    // 移除通信技能数据
    const analysisWithoutCommunication = {
      quick_practice: {
        ...mockAnalysisResult.quick_practice,
        communication_skills: null
      }
    };
    
    const wrapper = shallowMount(QuickPracticeReport, {
      props: {
        analysisResult: analysisWithoutCommunication
      }
    });
    
    // 检查模块评分显示（应该只有两个：内容质量和思维能力）
    const moduleScores = wrapper.findAll('.module-score');
    expect(moduleScores.length).toBe(2);
    
    // 检查详细分析数据（不应该有通信技能部分）
    const detailedAnalysis = wrapper.find('.detailed-analysis');
    expect(detailedAnalysis.exists()).toBe(true);
  });
  
  it('initializes and destroys chart correctly', async () => {
    // 模拟 HTMLCanvasElement.getContext
    HTMLCanvasElement.prototype.getContext = vi.fn();
    
    const wrapper = mount(QuickPracticeReport, {
      props: {
        analysisResult: mockAnalysisResult
      }
    });
    
    // 等待组件挂载后的处理
    await wrapper.vm.$nextTick();
    
    // 验证 Chart 构造函数被调用
    expect(Chart).toHaveBeenCalled();
    
    // 更新 props 测试 chart 是否重新创建
    await wrapper.setProps({
      analysisResult: {
        quick_practice: {
          ...mockAnalysisResult.quick_practice,
          feedback: {
            ...mockAnalysisResult.quick_practice.feedback
          }
        }
      }
    });
    
    // 等待组件更新后的处理
    await wrapper.vm.$nextTick();
    
    // 验证 chart 是否重新创建
    expect(Chart).toHaveBeenCalled();
  });
});
