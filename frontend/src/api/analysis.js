import request from '@/utils/request';

/**
 * 获取分析结果列表
 * @param {Object} params 查询参数
 * @returns {Promise} 请求Promise
 */
export function getAnalysisList(params) {
  return request({
    url: '/api/v1/analyses',
    method: 'get',
    params
  });
}

/**
 * 获取特定分析结果
 * @param {Number} id 分析ID
 * @returns {Promise} 请求Promise
 */
export function getAnalysis(id) {
  return request({
    url: `/api/v1/analyses/${id}`,
    method: 'get'
  });
}

/**
 * 获取面试的分析结果
 * @param {Number} interviewId 面试ID
 * @returns {Promise} 请求Promise
 */
export function getAnalysisByInterview(interviewId) {
  return request({
    url: `/api/v1/analyses/interview/${interviewId}`,
    method: 'get'
  });
}

/**
 * 创建分析结果
 * @param {Object} data 分析数据
 * @returns {Promise} 请求Promise
 */
export function createAnalysis(data) {
  return request({
    url: '/api/v1/analyses',
    method: 'post',
    data
  });
}

/**
 * 更新分析结果
 * @param {Number} id 分析ID
 * @param {Object} data 分析数据
 * @returns {Promise} 请求Promise
 */
export function updateAnalysis(id, data) {
  return request({
    url: `/api/v1/analyses/${id}`,
    method: 'put',
    data
  });
}

/**
 * 删除分析结果
 * @param {Number} id 分析ID
 * @returns {Promise} 请求Promise
 */
export function deleteAnalysis(id) {
  return request({
    url: `/api/v1/analyses/${id}`,
    method: 'delete'
  });
}

/**
 * 提交快速练习回答进行分析
 * @param {Object} data 包含回答文本、面试ID、问题ID等信息
 * @param {File} audioFile 音频文件（可选）
 * @returns {Promise} 请求Promise
 */
export function analyzeQuickPractice(data, audioFile = null) {
  const formData = new FormData();
  formData.append('interview_id', data.interviewId);
  formData.append('question_id', data.questionId);
  formData.append('answer_text', data.answerText);
  
  if (data.jobDescription) {
    formData.append('job_description', data.jobDescription);
  }
  
  if (data.question) {
    formData.append('question', data.question);
  }
  
  if (audioFile) {
    formData.append('audio_file', audioFile);
  }
  
  return request({
    url: '/api/v1/analyses/quick-practice',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}