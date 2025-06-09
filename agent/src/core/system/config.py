# agent/core/config.py

from typing import Dict, Any, Optional
import os
import json

class AgentConfig:
    """智能体配置类
    
    负责加载和管理智能体的配置参数
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 默认配置
        self.default_config = {
            # 通用配置
            "general": {
                "debug": False,
                "log_level": "INFO",
                "temp_dir": "./temp"
            },
            
            # 语音分析配置
            "speech": {
                "use_xunfei": True,
                "clarity_weight": 0.3,
                "pace_weight": 0.3,
                "emotion_weight": 0.4,
                "sample_rate": 16000
            },
            
            # 视觉分析配置
            "visual": {
                "face_detection_model": "haarcascade",
                "expression_weight": 0.4,
                "eye_contact_weight": 0.3,
                "body_language_weight": 0.3,
                "frame_sample_rate": 5  # 每秒采样帧数
            },
            
            # 内容分析配置
            "content": {
                "model": "bert-base-chinese",
                "relevance_weight": 0.4,
                "structure_weight": 0.3,
                "key_points_weight": 0.3
            },
            
            # 综合分析配置
            "overall": {
                "speech_weight": 0.3,
                "visual_weight": 0.3,
                "content_weight": 0.4,
                "strengths_count": 3,  # 输出的优势数量
                "weaknesses_count": 3,  # 输出的劣势数量
                "suggestions_count": 5   # 输出的建议数量
            },
            
            # 外部服务配置
            "services": {
                "xunfei": {
                    "app_id": "",  # 需要从环境变量或配置文件中加载
                    "api_key": "",
                    "api_secret": "",
                    "ise_url": "https://api.xfyun.cn/v1/service/v1/ise",
                    "iat_url": "https://api.xfyun.cn/v1/service/v1/iat",
                    "emotion_url": "https://api.xfyun.cn/v1/service/v1/emotion"
                }
            },
            
            # 数据库配置
            "db": {
                "vector": {
                    "db_type": "faiss",
                    "path": "./vector_db",
                    "dimension": 768
                }
            },
            
            # 检索器配置
            "retriever": {
                "hybrid": {
                    "max_results": 10,
                    "vector_weight": 0.7,
                    "keyword_weight": 0.3
                }
            },
            
            # MCP配置
            "mcp": {
                "api_endpoint": "http://localhost:3000/api",
                "api_key": ""
            }
        }
        
        # 加载配置
        self.config = self.default_config.copy()
        
        # 如果提供了配置文件路径，则从文件加载配置
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        
        # 从环境变量加载敏感配置（如API密钥）
        self._load_from_env()
    
    def _load_from_file(self, config_path: str):
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
                # 递归更新配置
                self._update_config(self.config, file_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def _update_config(self, target: Dict, source: Dict):
        """递归更新配置
        
        Args:
            target: 目标配置字典
            source: 源配置字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 加载讯飞API配置
        if os.environ.get("XUNFEI_APPID"):
            self.config["services"]["xunfei"]["app_id"] = os.environ.get("XUNFEI_APPID")
        
        if os.environ.get("XUNFEI_API_KEY"):
            self.config["services"]["xunfei"]["api_key"] = os.environ.get("XUNFEI_API_KEY")
        
        if os.environ.get("XUNFEI_API_SECRET"):
            self.config["services"]["xunfei"]["api_secret"] = os.environ.get("XUNFEI_API_SECRET")
        
        if os.environ.get("XUNFEI_ISE_URL"):
            self.config["services"]["xunfei"]["ise_url"] = os.environ.get("XUNFEI_ISE_URL")
        
        if os.environ.get("XUNFEI_IAT_URL"):
            self.config["services"]["xunfei"]["iat_url"] = os.environ.get("XUNFEI_IAT_URL")
        
        if os.environ.get("XUNFEI_EMOTION_URL"):
            self.config["services"]["xunfei"]["emotion_url"] = os.environ.get("XUNFEI_EMOTION_URL")
            
        # 加载讯飞星火API URL配置
        if os.environ.get("SPARK_API_URL"):
            if "spark" not in self.config["services"]:
                self.config["services"]["spark"] = {}
            self.config["services"]["spark"]["api_url"] = os.environ.get("SPARK_API_URL")
        
        # 加载OpenAI API配置
        if "openai" not in self.config["services"]:
            self.config["services"]["openai"] = {}
            
        if os.environ.get("OPENAI_API_KEY"):
            self.config["services"]["openai"]["api_key"] = os.environ.get("OPENAI_API_KEY")
            
        if os.environ.get("OPENAI_API_BASE"):
            self.config["services"]["openai"]["api_base"] = os.environ.get("OPENAI_API_BASE")
            
        if os.environ.get("OPENAI_MODEL"):
            self.config["services"]["openai"]["default_model"] = os.environ.get("OPENAI_MODEL")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            section: 配置部分名称
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        return self.config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置部分
        
        Args:
            section: 配置部分名称
            
        Returns:
            Dict[str, Any]: 配置部分
        """
        return self.config.get(section, {})
    
    def set(self, section: str, key: str, value: Any):
        """设置配置值
        
        Args:
            section: 配置部分名称
            key: 配置键名
            value: 配置值
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
    
    def save(self, config_path: str):
        """保存配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取通用配置值
        
        Args:
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        # 首先在顶层查找
        if key in self.config:
            return self.config[key]
        
        # 然后在general部分查找
        return self.config.get("general", {}).get(key, default)
    
    def get_service_config(self, service: str, key: str, default: Any = None) -> Any:
        """获取服务配置值
        
        Args:
            service: 服务名称
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        return self.config.get("services", {}).get(service, {}).get(key, default)
    
    def get_db_config(self, db_type: str, key: str, default: Any = None) -> Any:
        """获取数据库配置
        
        Args:
            db_type: 数据库类型
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get("db", {}).get(db_type, {}).get(key, default)
    
    def get_retriever_config(self, retriever_type: str, key: str, default: Any = None) -> Any:
        """获取检索器配置值
        
        Args:
            retriever_type: 检索器类型
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        return self.config.get("retriever", {}).get(retriever_type, {}).get(key, default)
    
    def set_config(self, key: str, value: Any):
        """设置配置值（别名方法，用于测试兼容）
        
        Args:
            key: 配置键名
            value: 配置值
        """
        # 自动将配置放入对应部分
        if key.endswith("_weight") and "weight" in key:
            if "clarity" in key or "pace" in key or "emotion" in key:
                self.set("speech", key, value)
            elif "expression" in key or "eye_contact" in key or "body_language" in key:
                self.set("visual", key, value)
            elif "relevance" in key or "structure" in key or "key_points" in key:
                self.set("content", key, value)
            else:
                self.set("general", key, value)
        elif key == "use_xunfei":
            self.set("speech", key, value)
        else:
            self.set("general", key, value)
    
    def get_learning_config(self, key: str, default: Any = None) -> Any:
        """获取学习路径相关配置
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        if "learning_path" not in self.config:
            return default
            
        return self.config["learning_path"].get(key, default)