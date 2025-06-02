# 多模态面试评测智能体 - AI智能体模块

本模块为多模态面试评测系统的AI智能体部分，专门负责面试音视频和内容的智能分析功能。通过将AI功能从后端分离，实现了更清晰的架构和更灵活的调用方式。

## 技术栈
- **Python 3.9+**：主要开发语言
- **LangGraph**：工作流管理框架
- **NumPy & SciPy**：科学计算
- **librosa**：音频特征提取
- **OpenCV**：视觉分析
- **讯飞API**：语音评测与情感分析
- **自适应学习系统**：模型参数动态调整

## 目录结构
```
agent/
├── docs/            # 文档
├── src/             # 源代码
│   ├── analyzers/   # 分析器模块
│   │   ├── base/    # 基础分析器
│   │   ├── speech/  # 语音分析
│   │   ├── visual/  # 视觉分析
│   │   └── content/ # 内容分析
│   ├── core/        # 核心功能
│   │   ├── agent/   # 智能体定义
│   │   ├── system/  # 系统功能
│   │   └── workflow/# 工作流管理
│   ├── learning/    # 学习与适应
│   ├── nodes/       # 工作流节点
│   │   ├── executors/   # 执行节点
│   │   └── processors/  # 处理节点
│   ├── scenarios/   # 场景定义
│   ├── services/    # 外部服务
│   └── utils/       # 工具函数
├── tests/           # 测试
│   ├── unit/        # 单元测试
│   ├── integration/ # 集成测试
│   └── performance/ # 性能测试
├── __init__.py      # 包初始化
├── setup.py         # 安装配置
└── requirements.txt # 依赖列表
```

## 主要功能模块

### 分析器（Analyzers）
- **语音分析器**：评估语音清晰度、语速、情感等
- **视觉分析器**：分析面部表情、眼神接触、肢体语言等
- **内容分析器**：评估回答相关性、结构、关键点等

### 工作流节点（Nodes）
- **分析执行节点**：负责调用各类分析器执行具体分析任务
- **任务规划节点**：将复杂任务分解为子任务并确定执行顺序
- **适应节点**：实现面试智能体的适应性调整

### 核心功能（Core）
- **状态管理**：定义和管理工作流状态
- **智能体**：提供面向用户的API接口
- **工作流**：基于LangGraph的工作流定义

### 学习与适应（Learning）
- **适应管理器**：动态调整分析参数和阈值
- **性能监控**：监控分析性能并触发适应

## 安装与配置
### 环境要求
- Python 3.9+
- 适当的GPU支持（推荐但非必须）

### 安装步骤
1. 克隆项目并进入agent目录
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：
   - XUNFEI_APPID：讯飞API的应用ID
   - XUNFEI_API_KEY：讯飞API的密钥
   - XUNFEI_API_SECRET：讯飞API的安全密钥

### 开发安装
如需进行开发，可以使用可编辑模式安装：
```bash
pip install -e .
```

## 使用方法
### 基本用法
```python
from agent import InterviewAgent, AgentConfig

# 创建配置
config = AgentConfig()

# 创建智能体
agent = InterviewAgent(config)

# 分析面试
result = agent.analyze(
    video_path="path/to/video.mp4",
    audio_path="path/to/audio.wav",
    transcript="面试内容文本..."
)

# 获取分析结果
print(f"总体得分: {result.overall_score}")
print(f"语音得分: {result.speech_score}")
print(f"视觉得分: {result.visual_score}")
print(f"内容得分: {result.content_score}")
print(f"优势: {result.strengths}")
print(f"不足: {result.weaknesses}")
print(f"建议: {result.suggestions}")
```

### 高级用法
```python
# 自定义配置
custom_config = AgentConfig({
    "speech": {
        "clarity_weight": 0.4,
        "pace_weight": 0.3,
        "emotion_weight": 0.3
    },
    "visual": {
        "expression_weight": 0.5,
        "eye_contact_weight": 0.3,
        "body_language_weight": 0.2
    },
    "content": {
        "relevance_weight": 0.5,
        "structure_weight": 0.3,
        "key_points_weight": 0.2
    }
})

# 创建带自定义配置的智能体
agent = InterviewAgent(custom_config)

# 流式处理（实时分析）
for chunk in video_stream:
    partial_result = agent.analyze_stream(chunk)
    if partial_result:
        print(f"实时得分: {partial_result.score}")
```

## 测试
- 单元测试：`python -m pytest tests/unit`
- 集成测试：`python -m pytest tests/integration`
- 性能测试：`python -m pytest tests/performance`

## 性能优化
- **并行处理**：支持多任务并行执行
- **延迟加载**：分析器按需加载
- **资源管理**：自动释放不需要的资源
- **缓存机制**：避免重复计算

## 扩展能力
### 添加新分析器
1. 在`src/analyzers`下创建新的分析器类
2. 继承`Analyzer`基类并实现必要方法
3. 在`AnalyzerFactory`中注册新分析器

### 自定义工作流
1. 在`src/nodes`下添加新的节点
2. 在`src/core/workflow/graph.py`中更新工作流定义

## 常见问题
- **内存使用过高**：调整配置中的`max_workers`参数
- **分析速度慢**：检查是否启用了GPU加速
- **讯飞API连接失败**：检查API密钥和网络连接

## 贡献指南
1. Fork项目
2. 创建分支
3. 提交PR

---
> 本智能体模块与前端、后端共同组成完整的多模态面试评测系统。详细集成方式请参考`backend/README.md`。


