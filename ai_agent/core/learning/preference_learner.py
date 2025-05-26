"""用户偏好学习器模块

实现面试智能体的用户偏好学习功能，包括个性化评估标准、用户行为分析和偏好适应。
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict, Counter
from enum import Enum, auto

from ..data_structures import AnalysisResult, Task, TaskStatus


class PreferenceType(Enum):
    """偏好类型枚举"""
    EVALUATION_CRITERIA = auto()  # 评估标准偏好
    FEEDBACK_STYLE = auto()  # 反馈风格偏好
    ANALYSIS_FOCUS = auto()  # 分析重点偏好
    INTERACTION_MODE = auto()  # 交互模式偏好
    DIFFICULTY_LEVEL = auto()  # 难度级别偏好


@dataclass
class UserPreference:
    """用户偏好"""
    user_id: str
    preference_type: PreferenceType
    preference_key: str
    preference_value: Any
    confidence: float  # 偏好置信度
    frequency: int  # 出现频次
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class UserBehavior:
    """用户行为"""
    user_id: str
    session_id: str
    action_type: str  # 行为类型
    action_data: Dict[str, Any]  # 行为数据
    context: Dict[str, Any]  # 上下文信息
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PreferencePattern:
    """偏好模式"""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    preferences: Dict[str, Any]
    support: float  # 支持度
    confidence: float  # 置信度
    users: Set[str]  # 适用用户
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if isinstance(self.users, list):
            self.users = set(self.users)


class BehaviorAnalyzer:
    """行为分析器"""
    
    def __init__(self):
        self.behavior_patterns = {}
        self.action_sequences = defaultdict(list)
        
    def analyze_behavior(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析用户行为"""
        if not behaviors:
            return {}
        
        analysis = {
            'action_frequency': self._analyze_action_frequency(behaviors),
            'session_patterns': self._analyze_session_patterns(behaviors),
            'temporal_patterns': self._analyze_temporal_patterns(behaviors),
            'preference_indicators': self._extract_preference_indicators(behaviors)
        }
        
        return analysis
    
    def _analyze_action_frequency(self, behaviors: List[UserBehavior]) -> Dict[str, int]:
        """分析行为频次"""
        action_counts = Counter(behavior.action_type for behavior in behaviors)
        return dict(action_counts)
    
    def _analyze_session_patterns(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析会话模式"""
        session_data = defaultdict(list)
        
        for behavior in behaviors:
            session_data[behavior.session_id].append(behavior)
        
        patterns = {
            'avg_session_length': np.mean([len(session) for session in session_data.values()]),
            'common_sequences': self._find_common_sequences(session_data),
            'session_types': self._classify_sessions(session_data)
        }
        
        return patterns
    
    def _analyze_temporal_patterns(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析时间模式"""
        if not behaviors:
            return {}
        
        timestamps = [b.timestamp for b in behaviors if b.timestamp]
        
        if not timestamps:
            return {}
        
        # 分析使用时间分布
        hours = [t.hour for t in timestamps]
        weekdays = [t.weekday() for t in timestamps]
        
        patterns = {
            'peak_hours': Counter(hours).most_common(3),
            'active_weekdays': Counter(weekdays).most_common(3),
            'usage_frequency': len(timestamps) / max((max(timestamps) - min(timestamps)).days, 1)
        }
        
        return patterns
    
    def _extract_preference_indicators(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """提取偏好指标"""
        indicators = {
            'feedback_preferences': self._analyze_feedback_preferences(behaviors),
            'analysis_preferences': self._analyze_analysis_preferences(behaviors),
            'interaction_preferences': self._analyze_interaction_preferences(behaviors)
        }
        
        return indicators
    
    def _analyze_feedback_preferences(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析反馈偏好"""
        feedback_behaviors = [b for b in behaviors if b.action_type == 'feedback_interaction']
        
        if not feedback_behaviors:
            return {}
        
        preferences = {
            'detail_level': self._infer_detail_preference(feedback_behaviors),
            'feedback_style': self._infer_style_preference(feedback_behaviors),
            'response_time': self._analyze_response_time(feedback_behaviors)
        }
        
        return preferences
    
    def _analyze_analysis_preferences(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析分析偏好"""
        analysis_behaviors = [b for b in behaviors if b.action_type == 'analysis_request']
        
        if not analysis_behaviors:
            return {}
        
        # 分析用户关注的分析维度
        focus_areas = []
        for behavior in analysis_behaviors:
            if 'focus_areas' in behavior.action_data:
                focus_areas.extend(behavior.action_data['focus_areas'])
        
        preferences = {
            'preferred_dimensions': Counter(focus_areas).most_common(3),
            'analysis_depth': self._infer_depth_preference(analysis_behaviors),
            'comparison_preference': self._infer_comparison_preference(analysis_behaviors)
        }
        
        return preferences
    
    def _analyze_interaction_preferences(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析交互偏好"""
        interaction_behaviors = [b for b in behaviors if 'interaction' in b.action_type]
        
        if not interaction_behaviors:
            return {}
        
        preferences = {
            'interaction_frequency': len(interaction_behaviors),
            'preferred_channels': self._analyze_interaction_channels(interaction_behaviors),
            'response_expectations': self._analyze_response_expectations(interaction_behaviors)
        }
        
        return preferences
    
    def _find_common_sequences(self, session_data: Dict[str, List[UserBehavior]]) -> List[Tuple[str, int]]:
        """找到常见行为序列"""
        sequences = []
        
        for session_behaviors in session_data.values():
            if len(session_behaviors) >= 2:
                sequence = tuple(b.action_type for b in sorted(session_behaviors, key=lambda x: x.timestamp))
                sequences.append(sequence)
        
        return Counter(sequences).most_common(5)
    
    def _classify_sessions(self, session_data: Dict[str, List[UserBehavior]]) -> Dict[str, int]:
        """分类会话类型"""
        session_types = Counter()
        
        for session_behaviors in session_data.values():
            actions = [b.action_type for b in session_behaviors]
            
            if 'analysis_request' in actions and 'feedback_interaction' in actions:
                session_types['comprehensive'] += 1
            elif 'analysis_request' in actions:
                session_types['analysis_focused'] += 1
            elif 'feedback_interaction' in actions:
                session_types['feedback_focused'] += 1
            else:
                session_types['exploratory'] += 1
        
        return dict(session_types)
    
    def _infer_detail_preference(self, behaviors: List[UserBehavior]) -> str:
        """推断详细程度偏好"""
        detail_scores = []
        
        for behavior in behaviors:
            if 'detail_level' in behavior.action_data:
                detail_scores.append(behavior.action_data['detail_level'])
        
        if detail_scores:
            avg_detail = np.mean(detail_scores)
            if avg_detail > 0.7:
                return 'detailed'
            elif avg_detail > 0.4:
                return 'moderate'
            else:
                return 'brief'
        
        return 'unknown'
    
    def _infer_style_preference(self, behaviors: List[UserBehavior]) -> str:
        """推断风格偏好"""
        # 简化的风格推断逻辑
        return 'professional'  # 默认专业风格
    
    def _analyze_response_time(self, behaviors: List[UserBehavior]) -> float:
        """分析响应时间偏好"""
        response_times = []
        
        for behavior in behaviors:
            if 'response_time' in behavior.action_data:
                response_times.append(behavior.action_data['response_time'])
        
        return np.mean(response_times) if response_times else 0.0
    
    def _infer_depth_preference(self, behaviors: List[UserBehavior]) -> str:
        """推断分析深度偏好"""
        # 基于用户请求的分析类型推断
        return 'deep'  # 默认深度分析
    
    def _infer_comparison_preference(self, behaviors: List[UserBehavior]) -> bool:
        """推断比较偏好"""
        comparison_requests = sum(1 for b in behaviors if b.action_data.get('include_comparison', False))
        return comparison_requests > len(behaviors) * 0.3
    
    def _analyze_interaction_channels(self, behaviors: List[UserBehavior]) -> Dict[str, int]:
        """分析交互渠道偏好"""
        channels = Counter()
        
        for behavior in behaviors:
            channel = behavior.action_data.get('channel', 'default')
            channels[channel] += 1
        
        return dict(channels)
    
    def _analyze_response_expectations(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """分析响应期望"""
        expectations = {
            'immediate_response': 0,
            'detailed_analysis': 0,
            'follow_up_questions': 0
        }
        
        for behavior in behaviors:
            if behavior.action_data.get('expect_immediate', False):
                expectations['immediate_response'] += 1
            if behavior.action_data.get('request_details', False):
                expectations['detailed_analysis'] += 1
            if behavior.action_data.get('ask_followup', False):
                expectations['follow_up_questions'] += 1
        
        return expectations


class PreferenceLearner:
    """用户偏好学习器主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # 数据存储
        self.user_preferences = defaultdict(list)  # user_id -> List[UserPreference]
        self.user_behaviors = defaultdict(list)  # user_id -> List[UserBehavior]
        self.preference_patterns = []  # List[PreferencePattern]
        
        # 学习参数
        self.min_behavior_count = self.config.get('min_behavior_count', 10)
        self.preference_decay_rate = self.config.get('preference_decay_rate', 0.95)
        self.pattern_min_support = self.config.get('pattern_min_support', 0.1)
        
        # 保存路径
        self.save_path = Path(self.config.get('preference_save_path', 'models/preferences'))
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        # 加载历史数据
        self._load_preference_data()
    
    def record_behavior(self, 
                       user_id: str, 
                       session_id: str, 
                       action_type: str, 
                       action_data: Dict[str, Any],
                       context: Dict[str, Any] = None) -> None:
        """记录用户行为"""
        behavior = UserBehavior(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            action_data=action_data,
            context=context or {}
        )
        
        self.user_behaviors[user_id].append(behavior)
        
        # 保持行为历史大小
        max_behaviors = self.config.get('max_behaviors_per_user', 1000)
        if len(self.user_behaviors[user_id]) > max_behaviors:
            self.user_behaviors[user_id] = self.user_behaviors[user_id][-max_behaviors:]
        
        # 如果行为数量足够，触发偏好学习
        if len(self.user_behaviors[user_id]) >= self.min_behavior_count:
            self._update_user_preferences(user_id)
        
        self.logger.debug(f"记录用户行为: {user_id} - {action_type}")
    
    def learn_preferences(self, user_id: str) -> Dict[str, Any]:
        """学习用户偏好"""
        try:
            if user_id not in self.user_behaviors:
                return {'learned': False, 'reason': 'No behavior data'}
            
            behaviors = self.user_behaviors[user_id]
            
            if len(behaviors) < self.min_behavior_count:
                return {'learned': False, 'reason': 'Insufficient behavior data'}
            
            # 分析用户行为
            behavior_analysis = self.behavior_analyzer.analyze_behavior(behaviors)
            
            # 提取偏好
            preferences = self._extract_preferences_from_analysis(user_id, behavior_analysis)
            
            # 更新用户偏好
            self._update_preferences(user_id, preferences)
            
            # 发现偏好模式
            self._discover_preference_patterns()
            
            # 保存数据
            self._save_preference_data()
            
            return {
                'learned': True,
                'preferences_count': len(preferences),
                'behavior_analysis': behavior_analysis
            }
            
        except Exception as e:
            self.logger.error(f"学习用户偏好失败: {e}")
            return {'learned': False, 'error': str(e)}
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好"""
        if user_id not in self.user_preferences:
            return {}
        
        preferences = {}
        for pref in self.user_preferences[user_id]:
            if pref.preference_type not in preferences:
                preferences[pref.preference_type.name] = {}
            
            preferences[pref.preference_type.name][pref.preference_key] = {
                'value': pref.preference_value,
                'confidence': pref.confidence,
                'frequency': pref.frequency,
                'last_updated': pref.last_updated.isoformat()
            }
        
        return preferences
    
    def predict_preferences(self, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """预测用户偏好"""
        # 获取已知偏好
        known_preferences = self.get_user_preferences(user_id)
        
        # 基于模式预测未知偏好
        predicted_preferences = self._predict_from_patterns(user_id, context)
        
        # 合并偏好
        all_preferences = {**predicted_preferences, **known_preferences}
        
        return all_preferences
    
    def adapt_to_preferences(self, 
                           user_id: str, 
                           analysis_result: AnalysisResult,
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """根据偏好适应分析结果"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            if not preferences:
                return analysis_result.__dict__
            
            # 适应分析结果
            adapted_result = self._apply_preferences_to_result(analysis_result, preferences)
            
            return adapted_result
            
        except Exception as e:
            self.logger.error(f"偏好适应失败: {e}")
            return analysis_result.__dict__
    
    def get_preference_statistics(self) -> Dict[str, Any]:
        """获取偏好统计"""
        stats = {
            'total_users': len(self.user_preferences),
            'total_behaviors': sum(len(behaviors) for behaviors in self.user_behaviors.values()),
            'preference_types': {},
            'pattern_count': len(self.preference_patterns),
            'active_users': len([uid for uid, behaviors in self.user_behaviors.items() 
                               if behaviors and behaviors[-1].timestamp > datetime.now() - timedelta(days=30)])
        }
        
        # 统计偏好类型分布
        for preferences in self.user_preferences.values():
            for pref in preferences:
                pref_type = pref.preference_type.name
                if pref_type not in stats['preference_types']:
                    stats['preference_types'][pref_type] = 0
                stats['preference_types'][pref_type] += 1
        
        return stats
    
    def _update_user_preferences(self, user_id: str) -> None:
        """更新用户偏好"""
        try:
            behaviors = self.user_behaviors[user_id][-self.min_behavior_count:]
            behavior_analysis = self.behavior_analyzer.analyze_behavior(behaviors)
            preferences = self._extract_preferences_from_analysis(user_id, behavior_analysis)
            self._update_preferences(user_id, preferences)
        except Exception as e:
            self.logger.error(f"更新用户偏好失败: {e}")
    
    def _extract_preferences_from_analysis(self, 
                                         user_id: str, 
                                         analysis: Dict[str, Any]) -> List[UserPreference]:
        """从行为分析中提取偏好"""
        preferences = []
        
        # 提取反馈偏好
        feedback_prefs = analysis.get('preference_indicators', {}).get('feedback_preferences', {})
        if feedback_prefs:
            for key, value in feedback_prefs.items():
                if value and key != 'response_time':
                    pref = UserPreference(
                        user_id=user_id,
                        preference_type=PreferenceType.FEEDBACK_STYLE,
                        preference_key=key,
                        preference_value=value,
                        confidence=0.8,
                        frequency=1
                    )
                    preferences.append(pref)
        
        # 提取分析偏好
        analysis_prefs = analysis.get('preference_indicators', {}).get('analysis_preferences', {})
        if analysis_prefs:
            for key, value in analysis_prefs.items():
                if value:
                    pref = UserPreference(
                        user_id=user_id,
                        preference_type=PreferenceType.ANALYSIS_FOCUS,
                        preference_key=key,
                        preference_value=value,
                        confidence=0.7,
                        frequency=1
                    )
                    preferences.append(pref)
        
        # 提取交互偏好
        interaction_prefs = analysis.get('preference_indicators', {}).get('interaction_preferences', {})
        if interaction_prefs:
            for key, value in interaction_prefs.items():
                if value:
                    pref = UserPreference(
                        user_id=user_id,
                        preference_type=PreferenceType.INTERACTION_MODE,
                        preference_key=key,
                        preference_value=value,
                        confidence=0.6,
                        frequency=1
                    )
                    preferences.append(pref)
        
        return preferences
    
    def _update_preferences(self, user_id: str, new_preferences: List[UserPreference]) -> None:
        """更新偏好"""
        existing_prefs = {(p.preference_type, p.preference_key): p 
                         for p in self.user_preferences[user_id]}
        
        for new_pref in new_preferences:
            key = (new_pref.preference_type, new_pref.preference_key)
            
            if key in existing_prefs:
                # 更新现有偏好
                existing_pref = existing_prefs[key]
                existing_pref.preference_value = new_pref.preference_value
                existing_pref.confidence = (existing_pref.confidence * self.preference_decay_rate + 
                                          new_pref.confidence * (1 - self.preference_decay_rate))
                existing_pref.frequency += 1
                existing_pref.last_updated = datetime.now()
            else:
                # 添加新偏好
                self.user_preferences[user_id].append(new_pref)
    
    def _discover_preference_patterns(self) -> None:
        """发现偏好模式"""
        # 简化的模式发现逻辑
        # 在实际实现中，这里可以使用更复杂的机器学习算法
        pass
    
    def _predict_from_patterns(self, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于模式预测偏好"""
        # 简化的预测逻辑
        return {}
    
    def _apply_preferences_to_result(self, 
                                   analysis_result: AnalysisResult, 
                                   preferences: Dict[str, Any]) -> Dict[str, Any]:
        """将偏好应用到分析结果"""
        adapted_result = analysis_result.__dict__.copy()
        
        # 根据偏好调整结果展示
        feedback_prefs = preferences.get('FEEDBACK_STYLE', {})
        if 'detail_level' in feedback_prefs:
            detail_level = feedback_prefs['detail_level']['value']
            if detail_level == 'brief':
                # 简化结果
                adapted_result['recommendations'] = adapted_result.get('recommendations', [])[:3]
            elif detail_level == 'detailed':
                # 增加详细信息
                adapted_result['detailed_analysis'] = True
        
        return adapted_result
    
    def _save_preference_data(self) -> None:
        """保存偏好数据"""
        try:
            # 保存用户偏好
            prefs_file = self.save_path / "user_preferences.json"
            prefs_data = {}
            
            for user_id, preferences in self.user_preferences.items():
                prefs_data[user_id] = []
                for pref in preferences:
                    pref_dict = asdict(pref)
                    pref_dict['preference_type'] = pref.preference_type.name
                    pref_dict['last_updated'] = pref.last_updated.isoformat()
                    prefs_data[user_id].append(pref_dict)
            
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(prefs_data, f, ensure_ascii=False, indent=2)
            
            # 保存行为数据（仅最近的）
            behaviors_file = self.save_path / "user_behaviors.json"
            behaviors_data = {}
            
            for user_id, behaviors in self.user_behaviors.items():
                behaviors_data[user_id] = []
                for behavior in behaviors[-100:]:  # 只保存最近100个行为
                    behavior_dict = asdict(behavior)
                    behavior_dict['timestamp'] = behavior.timestamp.isoformat()
                    behaviors_data[user_id].append(behavior_dict)
            
            with open(behaviors_file, 'w', encoding='utf-8') as f:
                json.dump(behaviors_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("偏好数据保存成功")
            
        except Exception as e:
            self.logger.error(f"保存偏好数据失败: {e}")
    
    def _load_preference_data(self) -> None:
        """加载偏好数据"""
        try:
            # 加载用户偏好
            prefs_file = self.save_path / "user_preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs_data = json.load(f)
                    
                    for user_id, user_prefs in prefs_data.items():
                        preferences = []
                        for pref_dict in user_prefs:
                            pref_dict['preference_type'] = PreferenceType[pref_dict['preference_type']]
                            pref_dict['last_updated'] = datetime.fromisoformat(pref_dict['last_updated'])
                            preferences.append(UserPreference(**pref_dict))
                        
                        self.user_preferences[user_id] = preferences
            
            # 加载行为数据
            behaviors_file = self.save_path / "user_behaviors.json"
            if behaviors_file.exists():
                with open(behaviors_file, 'r', encoding='utf-8') as f:
                    behaviors_data = json.load(f)
                    
                    for user_id, user_behaviors in behaviors_data.items():
                        behaviors = []
                        for behavior_dict in user_behaviors:
                            behavior_dict['timestamp'] = datetime.fromisoformat(behavior_dict['timestamp'])
                            behaviors.append(UserBehavior(**behavior_dict))
                        
                        self.user_behaviors[user_id] = behaviors
            
            self.logger.info("偏好数据加载成功")
            
        except Exception as e:
            self.logger.error(f"加载偏好数据失败: {e}")