#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学习路径生成器示例

展示如何使用学习路径生成器生成个性化学习路径
"""

import asyncio
import json
import os
import logging
import sys
from typing import Dict, Any

# 将项目根目录添加到路径中，以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from xufei.agent.src.nodes.executors.learning_path_generator import (
    LearningPathGenerator, 
    LearningPathGeneratorInput
)
from xufei.agent.src.core.system.config import AgentConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 示例面试分析结果
EXAMPLE_ANALYSIS = {
    "language_skills": {
        "clarity": 0.75,
        "fluency": 0.82,
        "vocabulary": 0.68,
        "grammar": 0.72,
        "overall": 0.74
    },
    "technical_skills": {
        "algorithm": 0.65,
        "data_structures": 0.70,
        "system_design": 0.55,
        "coding": 0.68,
        "overall": 0.65
    },
    "communication_skills": {
        "articulation": 0.78,
        "coherence": 0.72,
        "engagement": 0.80,
        "listening": 0.85,
        "overall": 0.79
    },
    "interview_performance": {
        "confidence": 0.72,
        "preparation": 0.68,
        "problem_solving": 0.66,
        "adaptability": 0.75,
        "overall": 0.70
    },
    "strengths": [
        "良好的沟通能力",
        "积极的倾听态度",
        "能够清晰地表达思路"
    ],
    "weaknesses": [
        "系统设计知识不足",
        "算法解题速度较慢",
        "技术深度需要提升"
    ],
    "recommendations": [
        "加强系统设计学习",
        "增加算法训练",
        "补充计算机网络知识"
    ]
}

async def run_learning_path_generator():
    """运行学习路径生成器"""
    try:
        # 初始化配置
        config = AgentConfig()
        
        # 创建学习路径生成器
        generator = LearningPathGenerator(config)
        
        # 准备输入
        input_data = LearningPathGeneratorInput(
            analysis_result=EXAMPLE_ANALYSIS,
            job_position="后端工程师",
            tech_field="后端开发",
            time_constraint="三个月",
            focus_areas=["系统设计", "算法", "数据库"]
        )
        
        logger.info("开始生成学习路径...")
        
        # 生成学习路径
        output = await generator.generate(input_data)
        
        # 格式化输出
        formatted_output = json.dumps(output.dict(), ensure_ascii=False, indent=2)
        
        logger.info("学习路径生成完成！")
        
        # 保存到文件
        with open("learning_path_result.json", "w", encoding="utf-8") as f:
            f.write(formatted_output)
        
        logger.info("结果已保存到 learning_path_result.json")
        
        # 打印主要信息
        print("\n===== 学习需求报告 =====")
        report = output.learning_report
        for key, value in report.items():
            if isinstance(value, dict) and "area" in value:
                print(f"\n领域: {value['area']}")
                print(f"当前水平: {value['level']}")
                print(f"优先级: {value['priority']}")
                print(f"描述: {value['description']}")
        
        print("\n===== 学习路径 =====")
        for i, path in enumerate(output.learning_paths):
            print(f"\n--- 路径 {i+1}: {path.need.area} ---")
            print(f"时间线: {path.timeline}")
            
            print("\n里程碑:")
            for j, milestone in enumerate(path.milestones):
                print(f"{j+1}. {milestone}")
            
            print("\n推荐资源:")
            for j, resource in enumerate(path.resources[:3]):  # 只显示前3个资源
                print(f"{j+1}. {resource.title} ({resource.source}, {resource.level})")
                if resource.url:
                    print(f"   链接: {resource.url}")
                print(f"   描述: {resource.description[:100]}..." if len(resource.description) > 100 else f"   描述: {resource.description}")
        
        return output
        
    except Exception as e:
        logger.error(f"运行学习路径生成器失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_learning_path_generator()) 