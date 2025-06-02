# AI Agent 测试

本目录包含AI Agent项目的测试用例，使用pytest框架进行测试。

## 测试结构

- `test_speech_analyzer.py`: 语音分析器的单元测试
- `conftest.py`: pytest配置和通用测试夹具

## 语音分析器测试

`test_speech_analyzer.py`文件包含对`SpeechAnalyzer`类的全面测试，包括：

- 初始化测试
- 特征提取测试
- 清晰度分析测试
- 语速分析测试
- 情感分析测试
- 语音转文本测试
- 异常处理测试

测试使用mock技术模拟了讯飞服务和音频特征提取器的行为，确保测试的独立性和可重复性。

## 运行测试

### 安装依赖

```bash
pip install pytest pytest-mock
```

### 运行所有测试

在项目根目录下运行：

```bash
python -m pytest ai_agent/tests
```

### 运行特定测试文件

```bash
python -m pytest ai_agent/tests/test_speech_analyzer.py
```

### 运行特定测试函数

```bash
python -m pytest ai_agent/tests/test_speech_analyzer.py::test_init
```

### 查看详细输出

```bash
python -m pytest ai_agent/tests -v
```

## 测试覆盖率

可以使用pytest-cov插件查看测试覆盖率：

```bash
pip install pytest-cov
python -m pytest ai_agent/tests --cov=ai_agent
```