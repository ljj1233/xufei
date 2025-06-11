#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试MCP工具的简单脚本
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_tools_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

async def test_mcp_file_system_tool():
    """测试 MCP FileSystem Tool"""
    logger.info("测试 MCP FileSystem Tool...")
    
    # 创建测试目录
    test_dir = Path("./test_mcp_fs")
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文件
    test_file = test_dir / "test_file.txt"
    test_file.write_text("这是一个测试文件")
    
    # 读取文件
    try:
        from mcp_FileSystem_Tool_read_file import mcp_FileSystem_Tool_read_file
        content = mcp_FileSystem_Tool_read_file({"path": str(test_file)})
        logger.info(f"读取文件内容: {content}")
        assert content == "这是一个测试文件", "文件内容不匹配"
    except ImportError:
        logger.error("无法导入 mcp_FileSystem_Tool_read_file")
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
    
    # 清理测试文件
    if test_file.exists():
        test_file.unlink()
    
    # 清理测试目录
    if test_dir.exists():
        test_dir.rmdir()
    
    logger.info("MCP FileSystem Tool 测试完成")

async def test_mcp_memory_tool():
    """测试 MCP Memory Tool"""
    logger.info("测试 MCP Memory Tool...")
    
    try:
        # 创建实体
        from mcp_Memory_Tool_create_entities import mcp_Memory_Tool_create_entities
        entities = [
            {
                "name": "面试评估",
                "entityType": "系统功能",
                "observations": ["自动分析面试表现", "提供量化评分"]
            },
            {
                "name": "语音分析",
                "entityType": "分析模块",
                "observations": ["分析语速", "分析语调", "分析清晰度"]
            }
        ]
        result = mcp_Memory_Tool_create_entities({"entities": entities})
        logger.info(f"创建实体结果: {result}")
        
        # 创建关系
        from mcp_Memory_Tool_create_relations import mcp_Memory_Tool_create_relations
        relations = [
            {
                "from": "面试评估",
                "to": "语音分析",
                "relationType": "包含"
            }
        ]
        result = mcp_Memory_Tool_create_relations({"relations": relations})
        logger.info(f"创建关系结果: {result}")
        
        # 搜索节点
        from mcp_Memory_Tool_search_nodes import mcp_Memory_Tool_search_nodes
        result = mcp_Memory_Tool_search_nodes({"query": "面试"})
        logger.info(f"搜索节点结果: {result}")
        
        # 读取图谱
        from mcp_Memory_Tool_read_graph import mcp_Memory_Tool_read_graph
        result = mcp_Memory_Tool_read_graph({"random_string": "test"})
        logger.info(f"读取图谱结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    except ImportError as e:
        logger.error(f"导入 MCP Memory Tool 失败: {e}")
    except Exception as e:
        logger.error(f"测试 MCP Memory Tool 失败: {e}")
    
    logger.info("MCP Memory Tool 测试完成")

async def run_tests():
    """运行所有测试"""
    await test_mcp_file_system_tool()
    logger.info("\n" + "="*50 + "\n")
    await test_mcp_memory_tool()

if __name__ == "__main__":
    asyncio.run(run_tests())