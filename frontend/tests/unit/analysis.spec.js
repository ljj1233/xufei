import { setActivePinia, createPinia } from 'pinia';
import { useAnalysisStore } from '@/stores/analysis';
import { getAnalysisByInterview, analyzeQuickPractice } from '@/api/analysis';

// Mock API 调用
jest.mock('@/api/analysis');

describe('Analysis Store', () => {
  let store;
  
  beforeEach(() => {
    // 创建一个新的 Pinia 实例并使其激活
    setActivePinia(createPinia());
    store = useAnalysisStore();
  });
  
  it('should initialize with correct default state', () => {
    expect(store.analysisData).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.analysisType).toBe('standard');
  });
  
  it('should have correct getters', () => {
    expect(store.getAnalysisResult).toBeNull();
    expect(store.getQuickPracticeResult).toBeNull();
    expect(store.getStandardAnalysisResult).toBeNull();
    expect(store.getOverallScore).toBe(0);
    expect(store.hasAnalysisResult).toBe(false);
    expect(store.isLoading).toBe(false);
  });
  
  it('should set analysis type', () => {
    store.setAnalysisType('quick_practice');
    expect(store.analysisType).toBe('quick_practice');
  });
  
  it('should fetch analysis by interview', async () => {
    // Mock API response
    const mockAnalysis = {
      id: 1,
      interview_id: 2,
      analysis_type: 'quick_practice',
      quick_practice: {
        content_quality: {
          relevance: 7.5,
          depth_and_detail: 6.0,
          professionalism: 8.0
        },
        cognitive_skills: {
          logical_structure: 7.0,
          clarity_of_thought: 7.5
        },
        feedback: {
          strengths: [{ category: 'content_quality', item: 'relevance', description: 'Good' }],
          growth_areas: [{ category: 'content_quality', item: 'depth', description: 'Need improvement' }],
          content_quality_score: 75.0,
          cognitive_skills_score: 72.5,
          communication_skills_score: 0,
          overall_score: 70.0
        }
      }
    };
    
    getAnalysisByInterview.mockResolvedValue({ data: mockAnalysis });
    
    // Fetch analysis
    const result = await store.fetchAnalysisByInterview(2);
    
    // Check store state update
    expect(store.loading).toBe(false);
    expect(store.analysisData).toEqual(mockAnalysis);
    expect(store.analysisType).toBe('quick_practice');
    expect(result).toEqual(mockAnalysis);
    
    // Check getters
    expect(store.getAnalysisResult).toEqual(mockAnalysis);
    expect(store.getQuickPracticeResult).toEqual(mockAnalysis.quick_practice);
    expect(store.getOverallScore).toBe(70.0);
    expect(store.hasAnalysisResult).toBe(true);
  });
  
  it('should handle fetch analysis error', async () => {
    // Mock API error
    getAnalysisByInterview.mockRejectedValue(new Error('Network error'));
    
    // Fetch analysis
    const result = await store.fetchAnalysisByInterview(2);
    
    // Check store state update
    expect(store.loading).toBe(false);
    expect(store.error).toBe('Network error');
    expect(store.analysisData).toBeNull();
    expect(result).toBeNull();
  });
  
  it('should submit quick practice analysis', async () => {
    // Mock API response
    const mockAnalysis = {
      id: 1,
      interview_id: 2,
      analysis_type: 'quick_practice',
      quick_practice: {
        content_quality: {
          relevance: 8.0,
          depth_and_detail: 7.0,
          professionalism: 8.5
        },
        cognitive_skills: {
          logical_structure: 7.5,
          clarity_of_thought: 8.0
        },
        communication_skills: {
          fluency: 7.0,
          speech_rate: 7.5,
          vocal_energy: 6.5,
          conciseness: 6.5
        },
        feedback: {
          strengths: [{ category: 'content_quality', item: 'relevance', description: 'Excellent' }],
          growth_areas: [{ category: 'communication_skills', item: 'fluency', description: 'Need improvement' }],
          content_quality_score: 78.3,
          cognitive_skills_score: 77.5,
          communication_skills_score: 69.0,
          overall_score: 75.2
        }
      }
    };
    
    analyzeQuickPractice.mockResolvedValue({ data: mockAnalysis });
    
    // Submit analysis
    const data = {
      interviewId: 2,
      questionId: 1,
      answerText: 'Test answer',
      jobDescription: 'Test job'
    };
    const audioFile = new File(['test audio data'], 'test.wav', { type: 'audio/wav' });
    
    const result = await store.submitQuickPracticeAnalysis(data, audioFile);
    
    // Check store state update
    expect(store.loading).toBe(false);
    expect(store.analysisData).toEqual(mockAnalysis);
    expect(store.analysisType).toBe('quick_practice');
    expect(result).toEqual(mockAnalysis);
    
    // Verify API call
    expect(analyzeQuickPractice).toHaveBeenCalledWith(data, audioFile);
  });
  
  it('should reset state', () => {
    // Set some data first
    store.analysisData = { test: 'data' };
    store.loading = true;
    store.error = 'Some error';
    
    // Reset state
    store.resetState();
    
    // Verify reset
    expect(store.analysisData).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
  });
});
