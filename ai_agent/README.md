# 多模态面试评测智能体库

这是一个独立的AI智能体库，专门用于多模态面试评测系统的分析功能。通过将AI功能从后端分离，实现了更清晰的架构和更灵活的调用方式。智能体能够分析面试视频/音频，提供语音、视觉和内容多维度评估，并根据不同面试场景生成针对性的改进建议。

## 1. 设计理念

### 1.1 三层架构

项目采用三层架构设计：
- **AI智能体**：独立的分析引擎，负责所有智能分析功能
- **后端**：业务逻辑处理、数据存储和API提供
- **前端**：用户界面和交互体验

这种分离使得各部分职责明确，便于维护和扩展。

### 1.2 智能体设计原则

- **场景识别**：智能体能够识别不同的面试场景和分析需求
- **统一接口**：提供简洁一致的API，隐藏内部复杂性
- **可扩展性**：便于添加新的分析模型和功能
- **可配置性**：支持灵活配置不同的分析参数和模型

## 2. 目录结构

```
ai_agent/
├── core/                      # 核心功能
│   ├── analyzer.py            # 分析器基类
│   ├── agent.py               # 智能体主类
│   ├── config.py              # 配置管理
│   └── utils.py               # 工具函数
├── analyzers/                 # 各类分析器
│   ├── speech_analyzer.py     # 语音分析器
│   ├── visual_analyzer.py     # 视觉分析器
│   ├── content_analyzer.py    # 内容分析器
│   └── overall_analyzer.py    # 综合分析器
├── models/                    # 模型定义
│   ├── feature_models.py      # 特征提取模型
│   ├── analysis_models.py     # 分析结果模型
│   └── scenario_models.py     # 场景模型
├── services/                  # 外部服务集成
│   ├── xunfei_service.py      # 讯飞服务集成
│   └── model_service.py       # 模型服务集成
├── scenarios/                 # 场景定义
│   ├── tech_interview.py      # 技术面试场景
│   ├── tech_interview_suggestions.py # 技术面试建议库
│   ├── product_interview.py   # 产品面试场景
│   └── general_interview.py   # 通用面试场景
├── tests/                     # 测试代码
│   ├── test_analyzers.py      # 分析器测试
│   ├── test_scenarios.py      # 场景测试
│   └── test_integration.py    # 集成测试
├── examples/                  # 使用示例
│   ├── basic_usage.py         # 基本使用示例
│   └── custom_scenario.py     # 自定义场景示例
├── requirements.txt           # 依赖项
├── setup.py                   # 安装配置
└── README.md                  # 本文档
```

## 3. 核心功能

### 3.1 场景识别与分析

智能体支持多种面试场景，目前已实现：

- **技术面试场景**：针对技术岗位面试的专门分析，包括编程能力、系统设计和问题解决能力等方面的评估。

每个场景都有自己的识别逻辑、分析参数和建议生成系统。例如，技术面试场景会关注技术关键词的使用、回答的结构性和专业深度等。

### 3.2 智能建议系统

智能体内置了丰富的建议库，可以根据分析结果生成针对性的改进建议：

- **技术面试建议库**：包含编程能力、系统设计、问题解决能力、项目经验等多个维度的专业建议。
- **内容相关建议**：针对回答相关性、结构、专业术语使用和技术深度的建议。
- **表现相关建议**：针对语音清晰度、语速、情感表达、眼神接触等方面的建议。

建议系统会根据分析结果自动选择最相关的建议，确保反馈的针对性和实用性。用户可以通过以下方式扩展和自定义建议系统：

- **添加新的建议类别**：在`tech_interview_suggestions.py`中添加新的建议类别和内容
- **调整建议选择逻辑**：修改`get_custom_suggestions`方法中的建议选择逻辑
- **自定义建议数量**：通过分析参数中的`suggestions_count`控制返回的建议数量

## 4. 核心API

### 4.1 智能体初始化

```python
from ai_agent.core.agent import InterviewAgent

# 创建智能体实例
agent = InterviewAgent()

# 或者使用自定义配置
agent = InterviewAgent(config_path="path/to/config.json")
```

### 4.2 场景识别与分析

```python
# 自动识别场景并分析
result = agent.analyze(file_path="interview.mp4")

# 指定场景分析
result = agent.analyze(
    file_path="interview.mp4", 
    scenario="tech_interview"
)

# 自定义分析参数
result = agent.analyze(
    file_path="interview.mp4",
    scenario="tech_interview",
    params={
        "focus_areas": ["coding_skills", "system_design", "problem_solving"],
        "speech_weight": 0.2,        # 语音在技术面试中权重较低
        "visual_weight": 0.2,        # 视觉在技术面试中权重较低
        "content_weight": 0.6,       # 内容在技术面试中权重较高
        "strengths_count": 3,        # 返回3条优势
        "weaknesses_count": 3,       # 返回3条劣势
        "suggestions_count": 5       # 返回5条建议
    }
)
```

### 4.3 获取分析结果

```python
# 获取完整分析结果，包括技术面试的专业建议
full_result = result.get_full_analysis()

# 获取技术面试场景的专业建议
suggestions = result.get_suggestions()
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion}")

# 示例输出：
# 1. 技术回答应当结构清晰，可以采用'定义-原理-应用-优缺点'的框架
# 2. 在回答中适当使用专业技术术语，展示你的专业背景和知识深度
# 3. 编程面试中，先理解问题，再设计算法，最后才开始编码
# 4. 系统设计面试中，先澄清需求和约束，再进行高层设计
# 5. 准备一些你参与过的技术项目案例，使用STAR法则描述你的贡献和解决方案

# 获取特定维度的分析
speech_analysis = result.get_speech_analysis()
visual_analysis = result.get_visual_analysis()
content_analysis = result.get_content_analysis()

# 获取综合评分和建议
overall_score = result.get_overall_score()
strengths = result.get_strengths()
weaknesses = result.get_weaknesses()
suggestions = result.get_suggestions()
```

## 4. 与后端集成

后端应用可以通过以下方式集成AI智能体：

```python
from ai_agent.core.agent import InterviewAgent

# 在服务中初始化智能体
class AnalysisService:
    def __init__(self):
        self.agent = InterviewAgent()
    
    def analyze_interview(self, file_path, file_type):
        # 调用智能体进行分析
        result = self.agent.analyze(
            file_path=file_path,
            file_type=file_type
        )
        
        # 转换为后端所需的数据格式
        return {
            "speech": result.get_speech_analysis(),
            "visual": result.get_visual_analysis(),
            "content": result.get_content_analysis(),
            "overall": {
                "score": result.get_overall_score(),
                "strengths": result.get_strengths(),
                "weaknesses": result.get_weaknesses(),
                "suggestions": result.get_suggestions()
            }
        }
```

## 5. 扩展功能

### 5.1 添加新场景

创建新的场景类并注册到智能体：

```python
from ai_agent.core.scenario import InterviewScenario

class CustomInterviewScenario(InterviewScenario):
    def __init__(self):
        super().__init__(name="custom_scenario")
        
    def recognize(self, features):
        # 实现场景识别逻辑
        pass
        
    def get_analysis_params(self):
        # 返回该场景的分析参数
        return {
            "focus_areas": ["area1", "area2"],
            "metrics": {"metric1": 0.7, "metric2": 0.3}
        }

# 注册新场景
agent.register_scenario(CustomInterviewScenario())
```

### 5.2 添加新分析器

创建新的分析器并注册到智能体：

```python
from ai_agent.core.analyzer import Analyzer

class CustomAnalyzer(Analyzer):
    def __init__(self):
        super().__init__(name="custom_analyzer")
        
    def extract_features(self, data):
        # 实现特征提取逻辑
        pass
        
    def analyze(self, features, params=None):
        # 实现分析逻辑
        pass

# 注册新分析器
agent.register_analyzer(CustomAnalyzer())
```

## 6. 依赖项

主要依赖项包括：

- numpy
- opencv-python
- librosa
- torch
- transformers
- requests

详细依赖请参见 `requirements.txt`。

## 7. 许可证

[MIT License](LICENSE)