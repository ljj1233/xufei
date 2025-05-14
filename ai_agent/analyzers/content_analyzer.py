# ai_agent/analyzers/content_analyzer.py

from typing import Dict, Any, Optional, List
import re

from ..core.analyzer import Analyzer
from ..core.config import AgentConfig
from ..core.utils import normalize_score, weighted_average


class ContentAnalyzer(Analyzer):
    """内容分析器
    
    负责分析面试内容的质量，包括相关性、结构和关键点等
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化内容分析器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(name="content_analyzer", analyzer_type="content", config=config)
        
        # 加载模型配置
        self.model_name = self.get_config("model", "bert-base-chinese")
        
        # 初始化NLP模型（延迟加载）
        self._model = None
        self._tokenizer = None
    
    def _load_model(self):
        """加载NLP模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            
            # 将模型设置为评估模式
            self._model.eval()
            
            # 如果有GPU，将模型移至GPU
            if torch.cuda.is_available():
                self._model = self._model.cuda()
        
        except Exception as e:
            print(f"加载NLP模型失败: {e}")
            self._model = None
            self._tokenizer = None
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """提取文本特征
        
        从文本中提取特征
        
        Args:
            text: 文本内容
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        if not text:
            return {}
        
        # 基本文本特征
        features = {
            "text": text,
            "length": len(text),
            "word_count": len(text.split()),
            "sentence_count": len(re.split(r'[。！？.!?]', text)),
        }
        
        # 提取STAR结构特征（情境、任务、行动、结果）
        star_features = self._extract_star_features(text)
        features.update(star_features)
        
        # 提取关键词特征
        keywords = self._extract_keywords(text)
        features["keywords"] = keywords
        
        # 如果需要使用预训练模型提取更高级特征
        if self._model is None and self._tokenizer is None:
            self._load_model()
        
        if self._model is not None and self._tokenizer is not None:
            # 使用预训练模型提取文本嵌入
            try:
                import torch
                
                # 对文本进行编码
                inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                
                # 如果有GPU，将输入移至GPU
                if torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # 获取模型输出
                with torch.no_grad():
                    outputs = self._model(**inputs)
                
                # 使用最后一层隐藏状态的平均值作为文本嵌入
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                # 将嵌入转换为列表
                features["embeddings"] = embeddings.cpu().numpy().tolist()[0]
            
            except Exception as e:
                print(f"提取文本嵌入失败: {e}")
        
        return features
    
    def _extract_star_features(self, text: str) -> Dict[str, Any]:
        """提取STAR结构特征
        
        检测文本中是否包含STAR结构（情境、任务、行动、结果）
        
        Args:
            text: 文本内容
            
        Returns:
            Dict[str, Any]: STAR结构特征
        """
        # 简单的关键词匹配方法，实际应用中可以使用更复杂的NLP技术
        situation_keywords = ["当时", "背景", "情况", "环境", "面临", "遇到"]
        task_keywords = ["目标", "任务", "需要", "要求", "职责", "挑战"]
        action_keywords = ["采取", "行动", "做法", "措施", "方法", "步骤", "实施"]
        result_keywords = ["结果", "成果", "效果", "影响", "收获", "学到", "实现"]
        
        # 检查各部分是否存在
        has_situation = any(keyword in text for keyword in situation_keywords)
        has_task = any(keyword in text for keyword in task_keywords)
        has_action = any(keyword in text for keyword in action_keywords)
        has_result = any(keyword in text for keyword in result_keywords)
        
        # 计算STAR完整度
        star_parts = [has_situation, has_task, has_action, has_result]
        star_completeness = sum(star_parts) / len(star_parts)
        
        return {
            "has_situation": has_situation,
            "has_task": has_task,
            "has_action": has_action,
            "has_result": has_result,
            "star_completeness": star_completeness
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        从文本中提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取方法，实际应用中可以使用TF-IDF、TextRank等算法
        # 这里仅作为示例，返回一些常见的技术面试关键词
        common_keywords = [
            "算法", "数据结构", "编程", "开发", "设计", "架构", "测试", "调试",
            "优化", "性能", "效率", "安全", "可靠", "可扩展", "可维护", "团队",
            "协作", "沟通", "学习", "创新", "解决问题", "分析", "思考", "经验"
        ]
        
        # 返回文本中出现的关键词
        return [keyword for keyword in common_keywords if keyword in text]
    
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析内容特征
        
        根据提取的内容特征进行分析
        
        Args:
            features: 提取的内容特征
            params: 分析参数，如果为None则使用默认参数
            
        Returns:
            Dict[str, Any]: 内容分析结果
        """
        if not features or "text" not in features:
            return {
                "relevance": 5.0,
                "structure": 5.0,
                "key_points": [],
                "overall_score": 5.0
            }
        
        # 获取权重配置
        relevance_weight = self.get_config("relevance_weight", 0.4)
        structure_weight = self.get_config("structure_weight", 0.3)
        key_points_weight = self.get_config("key_points_weight", 0.3)
        
        # 如果提供了参数，覆盖默认权重
        if params:
            relevance_weight = params.get("relevance_weight", relevance_weight)
            structure_weight = params.get("structure_weight", structure_weight)
            key_points_weight = params.get("key_points_weight", key_points_weight)
        
        # 分析相关性
        relevance = self._analyze_relevance(features, params)
        
        # 分析结构
        structure = self._analyze_structure(features)
        
        # 分析关键点
        key_points, key_points_score = self._analyze_key_points(features)
        
        # 计算总分
        overall_score = weighted_average(
            {
                "relevance": relevance,
                "structure": structure,
                "key_points": key_points_score
            },
            {
                "relevance": relevance_weight,
                "structure": structure_weight,
                "key_points": key_points_weight
            }
        )
        
        return {
            "relevance": relevance,
            "structure": structure,
            "key_points": key_points,
            "key_points_score": key_points_score,
            "overall_score": overall_score
        }
    
    def _analyze_relevance(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> float:
        """分析相关性
        
        分析内容与面试主题的相关性
        
        Args:
            features: 内容特征
            params: 分析参数
            
        Returns:
            float: 相关性评分（0-10）
        """
        # 获取关键词
        keywords = features.get("keywords", [])
        
        # 如果参数中提供了期望关键词，则与之比较
        expected_keywords = []
        if params and "expected_keywords" in params:
            expected_keywords = params.get("expected_keywords", [])
        
        # 如果没有期望关键词，则使用一般技术面试关键词
        if not expected_keywords:
            expected_keywords = [
                "算法", "数据结构", "编程", "开发", "设计", "架构", "测试", "调试",
                "优化", "性能", "效率", "安全", "可靠", "可扩展", "可维护"
            ]
        
        # 计算关键词匹配度
        if expected_keywords:
            matched_keywords = [keyword for keyword in keywords if keyword in expected_keywords]
            keyword_match_ratio = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0
            
            # 根据关键词匹配度计算相关性评分
            relevance = 5.0 + 5.0 * keyword_match_ratio
        else:
            # 如果没有关键词信息，给予中等评分
            relevance = 5.0
        
        return normalize_score(relevance)
    
    def _analyze_structure(self, features: Dict[str, Any]) -> float:
        """分析结构
        
        分析内容的结构性
        
        Args:
            features: 内容特征
            
        Returns:
            float: 结构评分（0-10）
        """
        # 获取STAR结构完整度
        star_completeness = features.get("star_completeness", 0.0)
        
        # 获取句子数量
        sentence_count = features.get("sentence_count", 0)
        
        # 计算结构评分
        # STAR结构完整度占主要权重
        structure = 7.0 * star_completeness
        
        # 句子数量也影响结构评分，过少或过多都不理想
        if sentence_count < 3:
            # 句子太少，结构不完整
            structure *= 0.7
        elif sentence_count > 20:
            # 句子太多，可能结构混乱
            structure *= 0.9
        else:
            # 句子数量适中，加分
            structure *= 1.1
        
        # 确保评分在0-10范围内
        return normalize_score(structure)
    
    def _analyze_key_points(self, features: Dict[str, Any]) -> tuple:
        """分析关键点
        
        提取和评估内容中的关键点
        
        Args:
            features: 内容特征
            
        Returns:
            tuple: (关键点列表, 关键点评分)
        """
        # 获取文本和关键词
        text = features.get("text", "")
        keywords = features.get("keywords", [])
        
        # 简单的关键点提取方法，实际应用中可以使用更复杂的NLP技术
        key_points = []
        
        # 基于关键词提取关键点（简化处理）
        for keyword in keywords:
            # 查找包含关键词的句子
            sentences = re.split(r'[。！？.!?]', text)
            for sentence in sentences:
                if keyword in sentence and len(sentence) > 10:
                    # 简化处理：将包含关键词的句子作为关键点
                    key_point = sentence.strip()
                    if key_point and key_point not in key_points:
                        key_points.append(key_point)
                        break
        
        # 限制关键点数量
        key_points = key_points[:5]
        
        # 计算关键点评分
        if key_points:
            # 关键点数量影响评分
            key_points_score = 5.0 + 1.0 * len(key_points)
        else:
            key_points_score = 5.0
        
        return key_points, normalize_score(key_points_score)