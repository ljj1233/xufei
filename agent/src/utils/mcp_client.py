# agent/utils/mcp_client.py

from typing import Dict, Any, Optional, Union, List
import logging
import json
import asyncio
import subprocess
import os
import sys
import platform

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP客户端
    
    用于与MCP服务交互
    """
    
    def __init__(self):
        """初始化MCP客户端"""
        # 检查MCP配置文件
        self.mcp_config_path = self._get_mcp_config_path()
        self.mcp_servers = self._load_mcp_config()
        
        logger.info(f"MCP客户端初始化完成，发现 {len(self.mcp_servers)} 个服务")
    
    def _get_mcp_config_path(self) -> str:
        """获取MCP配置文件路径
        
        Returns:
            str: 配置文件路径
        """
        # 检查常见的MCP配置文件位置
        home_dir = os.path.expanduser("~")
        
        # Cursor的MCP配置文件位置
        cursor_config_path = os.path.join(home_dir, ".cursor", "mcp.json")
        if os.path.exists(cursor_config_path):
            return cursor_config_path
        
        # 其他可能的位置
        other_paths = [
            os.path.join(home_dir, ".config", "mcp.json"),
            os.path.join(os.getcwd(), "mcp.json")
        ]
        
        for path in other_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("未找到MCP配置文件")
        return ""
    
    def _load_mcp_config(self) -> Dict[str, Any]:
        """加载MCP配置
        
        Returns:
            Dict[str, Any]: MCP服务配置
        """
        if not self.mcp_config_path:
            return {}
        
        try:
            with open(self.mcp_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            # 提取服务配置
            if "mcpServers" in config:
                return config["mcpServers"]
            else:
                logger.warning("MCP配置文件中未找到mcpServers字段")
                return {}
                
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
            return {}
    
    def _get_server_config(self, server_id: str) -> Dict[str, Any]:
        """获取服务配置
        
        Args:
            server_id: 服务ID
            
        Returns:
            Dict[str, Any]: 服务配置
        """
        if server_id in self.mcp_servers:
            return self.mcp_servers[server_id]
        else:
            logger.error(f"未找到服务: {server_id}")
            return {}
    
    async def _start_server(self, server_id: str) -> Optional[subprocess.Popen]:
        """启动MCP服务
        
        Args:
            server_id: 服务ID
            
        Returns:
            Optional[subprocess.Popen]: 服务进程
        """
        server_config = self._get_server_config(server_id)
        if not server_config:
            return None
        
        try:
            # 获取命令和参数
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            if not command:
                logger.error(f"服务 {server_id} 未指定命令")
                return None
            
            # 合并环境变量
            full_env = os.environ.copy()
            full_env.update(env)
            
            # 启动服务
            logger.info(f"启动服务: {server_id}, 命令: {command} {' '.join(args)}")
            
            # 根据平台选择合适的方式启动
            if platform.system() == "Windows":
                # Windows下使用CREATE_NO_WINDOW标志
                process = subprocess.Popen(
                    [command] + args,
                    env=full_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Unix/Linux/Mac下使用普通方式
                process = subprocess.Popen(
                    [command] + args,
                    env=full_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # 等待服务启动
            await asyncio.sleep(2)
            
            return process
            
        except Exception as e:
            logger.error(f"启动服务 {server_id} 失败: {e}")
            return None
    
    async def call(self, server_id: str, function_name: str, params: Dict[str, Any]) -> Any:
        """调用MCP函数
        
        Args:
            server_id: 服务ID
            function_name: 函数名称
            params: 函数参数
            
        Returns:
            Any: 函数返回值
        """
        # 启动服务
        process = await self._start_server(server_id)
        if not process:
            logger.error(f"服务 {server_id} 启动失败")
            return {"error": f"服务 {server_id} 启动失败"}
        
        try:
            # 准备请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": function_name,
                "params": params
            }
            
            # 发送请求
            request_json = json.dumps(request)
            process.stdin.write(request_json.encode("utf-8") + b"\n")
            process.stdin.flush()
            
            # 读取响应
            response_line = process.stdout.readline().decode("utf-8").strip()
            
            # 解析响应
            response = json.loads(response_line)
            
            # 检查错误
            if "error" in response:
                logger.error(f"MCP调用错误: {response['error']}")
                return {"error": response["error"]}
            
            # 返回结果
            if "result" in response:
                return response["result"]
            else:
                logger.warning("MCP响应中没有结果")
                return {}
                
        except Exception as e:
            logger.error(f"MCP调用异常: {e}")
            return {"error": str(e)}
            
        finally:
            # 关闭服务
            try:
                process.terminate()
            except:
                pass 