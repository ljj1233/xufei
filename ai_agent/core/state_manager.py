#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态管理器

负责管理智能体的状态信息，包括：
1. 会话状态管理
2. 上下文信息维护
3. 历史记录存储
4. 状态持久化
"""

from typing import Dict, Any, Optional, List
import json
import time
import asyncio
import os
import pickle
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from pathlib import Path
import logging

from .state import GraphState, Task, AnalysisResult, TaskStatus


@dataclass
class SessionState:
    """会话状态数据类"""
    session_id: str
    session_type: str
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "active"  # active, paused, completed, error
    task_history: List[str] = field(default_factory=list)
    analysis_results: List[Dict[str, Any]] = field(default_factory=list)
    user_feedback: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """从字典创建"""
        return cls(**data)


@dataclass
class GlobalState:
    """全局状态数据类"""
    total_sessions: int = 0
    total_tasks: int = 0
    average_processing_time: float = 0.0
    success_rate: float = 0.0
    last_update: float = field(default_factory=time.time)
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalState':
        """从字典创建"""
        return cls(**data)


class StateManager:
    """状态管理器
    
    负责管理智能体的所有状态信息，提供状态的创建、更新、查询和持久化功能
    """
    
    def __init__(self, state_dir: str = "./state", auto_save_interval: int = 300):
        """初始化状态管理器
        
        Args:
            state_dir: 状态文件存储目录
            auto_save_interval: 自动保存间隔（秒）
        """
        self.state_dir = state_dir
        self.auto_save_interval = auto_save_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保状态目录存在
        os.makedirs(state_dir, exist_ok=True)
        
        # 状态存储
        self.sessions: Dict[str, SessionState] = {}
        self.global_state = GlobalState()
        
        # LangGraph状态存储
        self.graph_states: Dict[str, GraphState] = {}
        self.graph_state_cache: Dict[str, GraphState] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 3600  # 缓存1小时
        
        # 状态历史
        self.graph_state_history: Dict[str, List[GraphState]] = {}
        self.max_history_size = 10
        
        # 历史记录（内存中保留最近的记录）
        self.session_history = deque(maxlen=1000)
        self.task_history = deque(maxlen=5000)
        
        # 状态变更监听器
        self.state_listeners = []
        
        # 性能统计
        self.performance_stats = {
            "save_count": 0,
            "load_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_save_time": 0.0,
            "total_load_time": 0.0
        }
        
        # 加载已保存的状态
        self._load_state()
        
        # 启动自动保存任务
        self._start_auto_save()
    
    def _load_state(self):
        """加载已保存的状态"""
        try:
            # 加载全局状态
            global_state_file = os.path.join(self.state_dir, "global_state.json")
            if os.path.exists(global_state_file):
                with open(global_state_file, 'r', encoding='utf-8') as f:
                    global_data = json.load(f)
                    self.global_state = GlobalState.from_dict(global_data)
            
            # 加载活跃会话
            sessions_file = os.path.join(self.state_dir, "active_sessions.json")
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    sessions_data = json.load(f)
                    for session_id, session_data in sessions_data.items():
                        self.sessions[session_id] = SessionState.from_dict(session_data)
            
            # 加载历史记录
            self._load_history()
            
            self.logger.info(f"状态加载完成，活跃会话: {len(self.sessions)}")
            
        except Exception as e:
            self.logger.error(f"状态加载失败: {e}")
    
    def _load_history(self):
        """加载历史记录"""
        try:
            # 加载会话历史
            session_history_file = os.path.join(self.state_dir, "session_history.json")
            if os.path.exists(session_history_file):
                with open(session_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.session_history.extend(history_data[-1000:])  # 只加载最近1000条
            
            # 加载任务历史
            task_history_file = os.path.join(self.state_dir, "task_history.json")
            if os.path.exists(task_history_file):
                with open(task_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.task_history.extend(history_data[-5000:])  # 只加载最近5000条
                    
        except Exception as e:
            self.logger.warning(f"历史记录加载失败: {e}")
    
    def _start_auto_save(self):
        """启动自动保存任务"""
        async def auto_save_loop():
            while True:
                try:
                    await asyncio.sleep(self.auto_save_interval)
                    await self.save_state()
                except Exception as e:
                    self.logger.error(f"自动保存失败: {e}")
        
        asyncio.create_task(auto_save_loop())
    
    async def start_session(self, session_id: str, session_type: str, 
                           context: Optional[Dict[str, Any]] = None) -> bool:
        """开始新会话
        
        Args:
            session_id: 会话ID
            session_type: 会话类型
            context: 会话上下文
            
        Returns:
            bool: 是否成功创建
        """
        if session_id in self.sessions:
            self.logger.warning(f"会话 {session_id} 已存在")
            return False
        
        # 创建新会话状态
        session_state = SessionState(
            session_id=session_id,
            session_type=session_type,
            context=context or {},
            start_time=time.time()
        )
        
        self.sessions[session_id] = session_state
        
        # 更新全局状态
        self.global_state.total_sessions += 1
        self.global_state.last_update = time.time()
        
        # 通知监听器
        await self._notify_listeners("session_started", {
            "session_id": session_id,
            "session_type": session_type,
            "context": context
        })
        
        self.logger.info(f"会话 {session_id} 已开始")
        return True
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话总结
        """
        if session_id not in self.sessions:
            self.logger.warning(f"会话 {session_id} 不存在")
            return {}
        
        session_state = self.sessions[session_id]
        session_state.end_time = time.time()
        session_state.status = "completed"
        
        # 生成会话总结
        summary = self._generate_session_summary(session_state)
        
        # 移动到历史记录
        self.session_history.append(session_state.to_dict())
        
        # 从活跃会话中移除
        del self.sessions[session_id]
        
        # 更新全局状态
        self._update_global_metrics(session_state)
        
        # 通知监听器
        await self._notify_listeners("session_ended", {
            "session_id": session_id,
            "summary": summary
        })
        
        self.logger.info(f"会话 {session_id} 已结束")
        return summary
    
    def _generate_session_summary(self, session_state: SessionState) -> Dict[str, Any]:
        """生成会话总结
        
        Args:
            session_state: 会话状态
            
        Returns:
            Dict[str, Any]: 会话总结
        """
        duration = (session_state.end_time or time.time()) - session_state.start_time
        
        summary = {
            "session_id": session_state.session_id,
            "session_type": session_state.session_type,
            "duration": duration,
            "total_tasks": len(session_state.task_history),
            "total_results": len(session_state.analysis_results),
            "feedback_count": len(session_state.user_feedback),
            "performance_metrics": session_state.performance_metrics,
            "start_time": session_state.start_time,
            "end_time": session_state.end_time
        }
        
        # 计算平均分数（如果有分析结果）
        if session_state.analysis_results:
            scores = []
            for result in session_state.analysis_results:
                if "overall_score" in result:
                    scores.append(result["overall_score"])
            
            if scores:
                summary["average_score"] = sum(scores) / len(scores)
                summary["max_score"] = max(scores)
                summary["min_score"] = min(scores)
        
        # 分析用户反馈
        if session_state.user_feedback:
            positive_feedback = sum(1 for fb in session_state.user_feedback 
                                  if fb.get("rating", 0) >= 4)
            summary["satisfaction_rate"] = positive_feedback / len(session_state.user_feedback)
        
        return summary
    
    def _update_global_metrics(self, session_state: SessionState):
        """更新全局指标
        
        Args:
            session_state: 会话状态
        """
        # 更新任务总数
        self.global_state.total_tasks += len(session_state.task_history)
        
        # 更新平均处理时间
        if session_state.performance_metrics.get("processing_times"):
            times = session_state.performance_metrics["processing_times"]
            avg_time = sum(times) / len(times)
            
            # 计算加权平均
            total_weight = self.global_state.total_sessions
            current_avg = self.global_state.average_processing_time
            
            self.global_state.average_processing_time = (
                (current_avg * (total_weight - 1) + avg_time) / total_weight
            )
        
        # 更新成功率
        if session_state.analysis_results:
            successful_tasks = sum(1 for result in session_state.analysis_results 
                                 if result.get("success", True))
            session_success_rate = successful_tasks / len(session_state.analysis_results)
            
            # 计算加权平均成功率
            total_weight = self.global_state.total_sessions
            current_rate = self.global_state.success_rate
            
            self.global_state.success_rate = (
                (current_rate * (total_weight - 1) + session_success_rate) / total_weight
            )
        
        self.global_state.last_update = time.time()
    
    async def update_session_context(self, session_id: str, context_update: Dict[str, Any]):
        """更新会话上下文
        
        Args:
            session_id: 会话ID
            context_update: 上下文更新
        """
        if session_id not in self.sessions:
            self.logger.warning(f"会话 {session_id} 不存在")
            return
        
        session_state = self.sessions[session_id]
        session_state.context.update(context_update)
        
        # 通知监听器
        await self._notify_listeners("context_updated", {
            "session_id": session_id,
            "context_update": context_update
        })
    
    async def add_task_to_session(self, session_id: str, task_id: str):
        """向会话添加任务
        
        Args:
            session_id: 会话ID
            task_id: 任务ID
        """
        if session_id not in self.sessions:
            self.logger.warning(f"会话 {session_id} 不存在")
            return
        
        session_state = self.sessions[session_id]
        session_state.task_history.append(task_id)
        
        # 添加到全局任务历史
        self.task_history.append({
            "task_id": task_id,
            "session_id": session_id,
            "timestamp": time.time()
        })
    
    async def add_result_to_session(self, session_id: str, result: Dict[str, Any]):
        """向会话添加分析结果
        
        Args:
            session_id: 会话ID
            result: 分析结果
        """
        if session_id not in self.sessions:
            self.logger.warning(f"会话 {session_id} 不存在")
            return
        
        session_state = self.sessions[session_id]
        session_state.analysis_results.append(result)
        
        # 更新性能指标
        if "processing_time" in result:
            if "processing_times" not in session_state.performance_metrics:
                session_state.performance_metrics["processing_times"] = []
            session_state.performance_metrics["processing_times"].append(result["processing_time"])
    
    async def add_feedback_to_session(self, session_id: str, feedback: Dict[str, Any]):
        """向会话添加用户反馈
        
        Args:
            session_id: 会话ID
            feedback: 用户反馈
        """
        if session_id not in self.sessions:
            self.logger.warning(f"会话 {session_id} 不存在")
            return
        
        session_state = self.sessions[session_id]
        feedback["timestamp"] = time.time()
        session_state.user_feedback.append(feedback)
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[SessionState]: 会话状态，如果不存在则返回None
        """
        return self.sessions.get(session_id)
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话上下文
        """
        session_state = self.sessions.get(session_id)
        return session_state.context if session_state else {}
    
    def get_global_state(self) -> GlobalState:
        """获取全局状态
        
        Returns:
            GlobalState: 全局状态
        """
        return self.global_state
    
    def get_active_sessions(self) -> List[str]:
        """获取活跃会话列表
        
        Returns:
            List[str]: 活跃会话ID列表
        """
        return list(self.sessions.keys())
    
    def get_session_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取会话历史
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 会话历史记录
        """
        return list(self.session_history)[-limit:]
    
    def get_task_history(self, session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务历史
        
        Args:
            session_id: 会话ID，如果为None则返回所有任务
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 任务历史记录
        """
        if session_id:
            filtered_history = [task for task in self.task_history 
                              if task.get("session_id") == session_id]
            return filtered_history[-limit:]
        else:
            return list(self.task_history)[-limit:]
    
    async def update_strategy_weights(self, weights: Dict[str, float]):
        """更新策略权重
        
        Args:
            weights: 策略权重字典
        """
        self.global_state.strategy_weights.update(weights)
        self.global_state.last_update = time.time()
        
        # 通知监听器
        await self._notify_listeners("strategy_weights_updated", {
            "weights": weights
        })
    
    async def update_learned_patterns(self, patterns: Dict[str, Any]):
        """更新学习到的模式
        
        Args:
            patterns: 学习模式字典
        """
        self.global_state.learned_patterns.update(patterns)
        self.global_state.last_update = time.time()
        
        # 通知监听器
        await self._notify_listeners("patterns_updated", {
            "patterns": patterns
        })
    
    def add_state_listener(self, listener: Callable):
        """添加状态变更监听器
        
        Args:
            listener: 监听器函数
        """
        self.state_listeners.append(listener)
    
    def remove_state_listener(self, listener: Callable):
        """移除状态变更监听器
        
        Args:
            listener: 监听器函数
        """
        if listener in self.state_listeners:
            self.state_listeners.remove(listener)
    
    async def _notify_listeners(self, event_type: str, event_data: Dict[str, Any]):
        """通知状态变更监听器
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        for listener in self.state_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_type, event_data)
                else:
                    listener(event_type, event_data)
            except Exception as e:
                self.logger.error(f"状态监听器执行失败: {e}")
    
    async def save_state(self):
        """保存状态到文件"""
        try:
            # 保存全局状态
            global_state_file = os.path.join(self.state_dir, "global_state.json")
            with open(global_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.global_state.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存活跃会话
            sessions_file = os.path.join(self.state_dir, "active_sessions.json")
            sessions_data = {sid: state.to_dict() for sid, state in self.sessions.items()}
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, ensure_ascii=False, indent=2)
            
            # 保存历史记录
            await self._save_history()
            
            self.logger.debug("状态保存完成")
            
        except Exception as e:
            self.logger.error(f"状态保存失败: {e}")
    
    async def _save_history(self):
        """保存历史记录"""
        try:
            # 保存会话历史
            session_history_file = os.path.join(self.state_dir, "session_history.json")
            with open(session_history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.session_history), f, ensure_ascii=False, indent=2)
            
            # 保存任务历史
            task_history_file = os.path.join(self.state_dir, "task_history.json")
            with open(task_history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.task_history), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.warning(f"历史记录保存失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        active_sessions = len(self.sessions)
        total_sessions = self.global_state.total_sessions
        
        # 计算会话类型分布
        session_types = defaultdict(int)
        for session in self.sessions.values():
            session_types[session.session_type] += 1
        
        # 计算最近的性能指标
        recent_sessions = list(self.session_history)[-50:]  # 最近50个会话
        recent_durations = []
        recent_scores = []
        
        for session_data in recent_sessions:
            if "duration" in session_data:
                recent_durations.append(session_data["duration"])
            if "average_score" in session_data:
                recent_scores.append(session_data["average_score"])
        
        statistics = {
            "active_sessions": active_sessions,
            "total_sessions": total_sessions,
            "total_tasks": self.global_state.total_tasks,
            "average_processing_time": self.global_state.average_processing_time,
            "success_rate": self.global_state.success_rate,
            "session_types": dict(session_types),
            "recent_performance": {
                "average_duration": sum(recent_durations) / len(recent_durations) if recent_durations else 0,
                "average_score": sum(recent_scores) / len(recent_scores) if recent_scores else 0,
                "session_count": len(recent_sessions)
            },
            "last_update": self.global_state.last_update
        }
        
        return statistics
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止自动保存
            if hasattr(self, '_auto_save_task') and self._auto_save_task:
                self._auto_save_task.cancel()
            
            # 保存当前状态
            self.save_state()
            
            # 优化存储
            self.optimize_storage()
            
            self.logger.info("状态管理器清理完成")
            
        except Exception as e:
            self.logger.error(f"状态管理器清理失败: {e}")
    
    # LangGraph状态管理方法
    
    def save_graph_state(self, session_id: str, state: GraphState, 
                        format: str = "pickle") -> bool:
        """保存LangGraph状态
        
        Args:
            session_id: 会话ID
            state: 要保存的图状态
            format: 保存格式 ('pickle' 或 'json')
            
        Returns:
            bool: 保存是否成功
        """
        start_time = time.time()
        
        try:
            # 创建会话目录
            session_dir = Path(self.state_dir) / "graph_states" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graph_state_{timestamp}.{format}"
            filepath = session_dir / filename
            
            # 保存状态
            if format == "pickle":
                with open(filepath, 'wb') as f:
                    pickle.dump(state, f)
            elif format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self._graph_state_to_dict(state), f, 
                             ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            # 更新缓存
            self.graph_state_cache[session_id] = state
            self.cache_timestamps[session_id] = time.time()
            
            # 更新历史
            if session_id not in self.graph_state_history:
                self.graph_state_history[session_id] = []
            
            self.graph_state_history[session_id].append(state)
            if len(self.graph_state_history[session_id]) > self.max_history_size:
                self.graph_state_history[session_id].pop(0)
            
            # 更新统计
            self.performance_stats["save_count"] += 1
            self.performance_stats["total_save_time"] += time.time() - start_time
            
            self.logger.debug(f"图状态保存成功: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存图状态失败: {e}")
            return False
    
    def load_graph_state(self, session_id: str, 
                        timestamp: Optional[str] = None) -> Optional[GraphState]:
        """加载LangGraph状态
        
        Args:
            session_id: 会话ID
            timestamp: 时间戳，如果为None则加载最新状态
            
        Returns:
            GraphState: 加载的状态，失败时返回None
        """
        start_time = time.time()
        
        try:
            # 检查缓存
            if (session_id in self.graph_state_cache and 
                self._is_cache_valid(session_id)):
                self.performance_stats["cache_hits"] += 1
                return self.graph_state_cache[session_id]
            
            self.performance_stats["cache_misses"] += 1
            
            # 从文件加载
            session_dir = Path(self.state_dir) / "graph_states" / session_id
            if not session_dir.exists():
                return None
            
            # 查找状态文件
            state_files = list(session_dir.glob("graph_state_*.pickle")) + \
                         list(session_dir.glob("graph_state_*.json"))
            
            if not state_files:
                return None
            
            # 选择文件
            if timestamp:
                target_file = None
                for file in state_files:
                    if timestamp in file.name:
                        target_file = file
                        break
                if not target_file:
                    return None
            else:
                # 选择最新文件
                target_file = max(state_files, key=lambda f: f.stat().st_mtime)
            
            # 加载状态
            if target_file.suffix == ".pickle":
                with open(target_file, 'rb') as f:
                    state = pickle.load(f)
            elif target_file.suffix == ".json":
                with open(target_file, 'r', encoding='utf-8') as f:
                    state_dict = json.load(f)
                    state = self._dict_to_graph_state(state_dict)
            else:
                return None
            
            # 更新缓存
            self.graph_state_cache[session_id] = state
            self.cache_timestamps[session_id] = time.time()
            
            # 更新统计
            self.performance_stats["load_count"] += 1
            self.performance_stats["total_load_time"] += time.time() - start_time
            
            self.logger.debug(f"图状态加载成功: {session_id}")
            return state
            
        except Exception as e:
            self.logger.error(f"加载图状态失败: {e}")
            return None
    
    def get_graph_state_history(self, session_id: str) -> List[GraphState]:
        """获取图状态历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[GraphState]: 状态历史列表
        """
        return self.graph_state_history.get(session_id, [])
    
    def rollback_graph_state(self, session_id: str, steps: int = 1) -> Optional[GraphState]:
        """回滚图状态
        
        Args:
            session_id: 会话ID
            steps: 回滚步数
            
        Returns:
            GraphState: 回滚后的状态
        """
        history = self.graph_state_history.get(session_id, [])
        if len(history) <= steps:
            return None
        
        target_state = history[-(steps + 1)]
        
        # 更新缓存
        self.graph_state_cache[session_id] = target_state
        self.cache_timestamps[session_id] = time.time()
        
        self.logger.info(f"图状态回滚成功: {session_id}, 步数: {steps}")
        return target_state
    
    def clear_graph_cache(self, session_id: Optional[str] = None):
        """清理图状态缓存
        
        Args:
            session_id: 会话ID，如果为None则清理所有缓存
        """
        if session_id:
            self.graph_state_cache.pop(session_id, None)
            self.cache_timestamps.pop(session_id, None)
        else:
            self.graph_state_cache.clear()
            self.cache_timestamps.clear()
        
        self.logger.debug(f"图状态缓存清理完成: {session_id or 'all'}")
    
    def optimize_storage(self):
        """优化存储
        
        压缩旧文件，清理重复状态等
        """
        try:
            # 清理过期缓存
            current_time = time.time()
            expired_sessions = []
            
            for session_id, timestamp in self.cache_timestamps.items():
                if current_time - timestamp > self.cache_ttl:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.graph_state_cache.pop(session_id, None)
                self.cache_timestamps.pop(session_id, None)
            
            # 清理旧状态文件
            self._cleanup_old_graph_states()
            
            self.logger.info(f"存储优化完成，清理了 {len(expired_sessions)} 个过期缓存")
            
        except Exception as e:
            self.logger.error(f"存储优化失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        stats = self.performance_stats.copy()
        
        # 计算平均时间
        if stats["save_count"] > 0:
            stats["avg_save_time"] = stats["total_save_time"] / stats["save_count"]
        else:
            stats["avg_save_time"] = 0.0
        
        if stats["load_count"] > 0:
            stats["avg_load_time"] = stats["total_load_time"] / stats["load_count"]
        else:
            stats["avg_load_time"] = 0.0
        
        # 计算缓存命中率
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        if total_requests > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_requests
        else:
            stats["cache_hit_rate"] = 0.0
        
        return stats
    
    def _is_cache_valid(self, session_id: str) -> bool:
        """检查缓存是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 缓存是否有效
        """
        if session_id not in self.cache_timestamps:
            return False
        
        return time.time() - self.cache_timestamps[session_id] < self.cache_ttl
    
    def _cleanup_old_graph_states(self, days: int = 7):
        """清理旧的图状态文件
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        graph_states_dir = Path(self.state_dir) / "graph_states"
        
        if not graph_states_dir.exists():
            return
        
        for session_dir in graph_states_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            for state_file in session_dir.glob("graph_state_*"):
                file_time = datetime.fromtimestamp(state_file.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        state_file.unlink()
                    except Exception as e:
                        self.logger.warning(f"删除旧图状态文件失败: {e}")
    
    def _graph_state_to_dict(self, state: GraphState) -> Dict[str, Any]:
        """将图状态转换为字典
        
        Args:
            state: 图状态
            
        Returns:
            Dict[str, Any]: 状态字典
        """
        return {
            "current_task": self._task_to_dict(state.current_task) if state.current_task else None,
            "tasks": [self._task_to_dict(task) for task in state.tasks],
            "analysis_results": [self._result_to_dict(result) for result in state.analysis_results],
            "user_context": state.user_context.__dict__ if state.user_context else None,
            "feedback_state": state.feedback_state.__dict__ if state.feedback_state else None,
            "analysis_state": state.analysis_state.__dict__ if state.analysis_state else None,
            "task_state": state.task_state.__dict__ if state.task_state else None,
            "metadata": state.metadata
        }
    
    def _dict_to_graph_state(self, state_dict: Dict[str, Any]) -> GraphState:
        """将字典转换为图状态
        
        Args:
            state_dict: 状态字典
            
        Returns:
            GraphState: 图状态
        """
        state = GraphState()
        
        # 恢复任务
        if state_dict.get("current_task"):
            state.current_task = self._dict_to_task(state_dict["current_task"])
        
        state.tasks = [self._dict_to_task(task_dict) 
                      for task_dict in state_dict.get("tasks", [])]
        
        # 恢复分析结果
        state.analysis_results = [self._dict_to_result(result_dict)
                                 for result_dict in state_dict.get("analysis_results", [])]
        
        # 恢复其他状态
        state.metadata = state_dict.get("metadata", {})
        
        return state
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """将任务转换为字典"""
        return {
            "id": task.id,
            "type": task.type.value,
            "priority": task.priority.value,
            "status": task.status.value,
            "data": task.data,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "metadata": task.metadata
        }
    
    def _dict_to_task(self, task_dict: Dict[str, Any]) -> Task:
        """将字典转换为任务"""
        from .state import TaskType, TaskPriority
        
        task = Task(
            type=TaskType(task_dict["type"]),
            priority=TaskPriority(task_dict["priority"]),
            data=task_dict["data"]
        )
        task.id = task_dict["id"]
        task.status = TaskStatus(task_dict["status"])
        task.created_at = datetime.fromisoformat(task_dict["created_at"])
        if task_dict.get("updated_at"):
            task.updated_at = datetime.fromisoformat(task_dict["updated_at"])
        task.metadata = task_dict.get("metadata", {})
        
        return task
    
    def _result_to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """将分析结果转换为字典"""
        return {
            "task_id": result.task_id,
            "task_type": result.task_type.value,
            "score": result.score,
            "confidence": result.confidence,
            "details": result.details,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata
        }
    
    def _dict_to_result(self, result_dict: Dict[str, Any]) -> AnalysisResult:
        """将字典转换为分析结果"""
        from .state import TaskType
        
        return AnalysisResult(
            task_id=result_dict["task_id"],
            task_type=TaskType(result_dict["task_type"]),
            score=result_dict["score"],
            confidence=result_dict["confidence"],
            details=result_dict["details"],
            timestamp=datetime.fromisoformat(result_dict["timestamp"]),
            metadata=result_dict.get("metadata", {})
        )