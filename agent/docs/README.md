# 面试智能体项目

## 项目介绍

面试智能体是一个基于AI的面试分析系统，可以对面试过程中的语音、视觉和内容进行全方位分析，为面试者提供专业的反馈和建议。

## 主要功能

1. **语音分析**：分析语速、清晰度、情感等语音特征
2. **视觉分析**：分析面部表情、眼神接触、肢体语言等视觉特征
3. **内容分析**：分析回答的相关性、完整性、结构等内容特征
4. **综合分析**：结合多维度分析结果，生成全面的面试评估报告

## 系统架构

- **分析器模块**：负责各类特征的提取和分析
  - 语音分析器（SpeechAnalyzer）
  - 视觉分析器（VisualAnalyzer）
  - 内容分析器（ContentAnalyzer）
  
- **工作流模块**：协调各分析器的工作，处理面试分析流程
  - 同步分析流程
  - 异步分析流程
  
- **服务模块**：提供各种基础服务
  - 讯飞服务（XunFeiService）
  - 内容过滤服务（ContentFilterService）
  - 通知服务（NotificationService）

## 测试状态

项目包含多种类型的测试，确保系统的稳定性和可靠性：

- **单元测试**：测试各个组件的独立功能
- **集成测试**：测试组件间的协作
- **性能测试**：测试系统在各种负载下的性能表现

当前测试状态：

✅ 工作流测试（test_workflow.py）  
✅ 集成测试（test_integration_workflow.py）  
✅ 内容分析器测试（test_content_analyzer.py）  
❌ 语音分析器测试（test_speech_analyzer.py）  
❌ 性能测试（test_performance.py）  
❌ MCP测试  

详细的测试修复记录请参考 [fixes.md](./fixes.md)

## 环境配置

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
# 讯飞API配置
export XUNFEI_APPID=your_app_id
export XUNFEI_API_KEY=your_api_key
export XUNFEI_API_SECRET=your_api_secret

# OpenAI API配置（可选）
export OPENAI_API_KEY=your_openai_key
```

## 运行测试

```bash
# 运行所有测试
cd tests
python run_tests.py

# 运行特定测试
pytest tests/test_workflow.py -v
pytest tests/test_integration_workflow.py -v
pytest tests/test_content_analyzer.py -v
``` 