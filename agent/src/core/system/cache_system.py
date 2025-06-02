#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存系统

提供多层次的缓存功能，包括：
1. 内存缓存
2. 文件缓存
3. 分析结果缓存
4. 会话状态缓存
5. 缓存策略管理
6. 缓存性能监控
"""

import time
import json
import pickle
import hashlib
import threading
import os
from typing import Any, Dict, Optional, Union, Callable, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from abc import ABC, abstractmethod
import weakref
import logging
from concurrent.futures import ThreadPoolExecutor


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """更新访问时间"""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """获取缓存年龄（秒）"""
        return time.time() - self.created_at


class CacheStrategy(ABC):
    """缓存策略抽象基类"""
    
    @abstractmethod
    def should_evict(self, entries: Dict[str, CacheEntry], 
                    new_entry_size: int) -> List[str]:
        """决定应该驱逐哪些缓存条目"""
        pass


class LRUStrategy(CacheStrategy):
    """最近最少使用策略"""
    
    def should_evict(self, entries: Dict[str, CacheEntry], 
                    new_entry_size: int) -> List[str]:
        # 按访问时间排序，最久未访问的排在前面
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1].accessed_at
        )
        
        to_evict = []
        for key, entry in sorted_entries:
            to_evict.append(key)
            if len(to_evict) >= len(entries) // 4:  # 驱逐25%的条目
                break
        
        return to_evict


class LFUStrategy(CacheStrategy):
    """最少使用频率策略"""
    
    def should_evict(self, entries: Dict[str, CacheEntry], 
                    new_entry_size: int) -> List[str]:
        # 按访问次数排序，访问次数最少的排在前面
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1].access_count
        )
        
        to_evict = []
        for key, entry in sorted_entries:
            to_evict.append(key)
            if len(to_evict) >= len(entries) // 4:  # 驱逐25%的条目
                break
        
        return to_evict


class TTLStrategy(CacheStrategy):
    """基于TTL的策略"""
    
    def should_evict(self, entries: Dict[str, CacheEntry], 
                    new_entry_size: int) -> List[str]:
        # 首先驱逐已过期的条目
        to_evict = []
        for key, entry in entries.items():
            if entry.is_expired():
                to_evict.append(key)
        
        # 如果还需要更多空间，按年龄驱逐
        if len(to_evict) < len(entries) // 4:
            remaining_entries = {
                k: v for k, v in entries.items() 
                if k not in to_evict
            }
            
            sorted_entries = sorted(
                remaining_entries.items(),
                key=lambda x: x[1].created_at
            )
            
            for key, entry in sorted_entries:
                to_evict.append(key)
                if len(to_evict) >= len(entries) // 4:
                    break
        
        return to_evict


class MemoryCache:
    """内存缓存"""
    
    def __init__(self, max_size: int = 1000, max_memory: int = 100 * 1024 * 1024,
                 default_ttl: Optional[float] = None, 
                 strategy: CacheStrategy = None):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大条目数
            max_memory: 最大内存使用（字节）
            default_ttl: 默认TTL（秒）
            strategy: 缓存策略
        """
        self.max_size = max_size
        self.max_memory = max_memory
        self.default_ttl = default_ttl
        self.strategy = strategy or LRUStrategy()
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._current_memory = 0
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0,
            'total_size': 0
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_size(self, value: Any) -> int:
        """计算值的大小"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, dict):
                return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
            else:
                return len(pickle.dumps(value))
        except Exception:
            return 1024  # 默认大小
    
    def _cleanup_expired(self):
        """清理过期条目"""
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
            self.stats['expired'] += 1
    
    def _remove_entry(self, key: str):
        """移除缓存条目"""
        if key in self._cache:
            entry = self._cache[key]
            self._current_memory -= entry.size
            del self._cache[key]
    
    def _evict_if_needed(self, new_entry_size: int):
        """如果需要则驱逐条目"""
        # 检查是否需要驱逐
        need_evict = (
            len(self._cache) >= self.max_size or
            self._current_memory + new_entry_size > self.max_memory
        )
        
        if need_evict:
            to_evict = self.strategy.should_evict(self._cache, new_entry_size)
            for key in to_evict:
                self._remove_entry(key)
                self.stats['evictions'] += 1
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        with self._lock:
            # 清理过期条目
            self._cleanup_expired()
            
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.touch()
                    self.stats['hits'] += 1
                    return entry.value
                else:
                    self._remove_entry(key)
                    self.stats['expired'] += 1
            
            self.stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            # 计算大小
            size = self._calculate_size(value)
            
            # 检查单个条目是否太大
            if size > self.max_memory:
                self.logger.warning(f"缓存条目太大，无法存储: {key} ({size} bytes)")
                return False
            
            # 如果键已存在，先移除
            if key in self._cache:
                self._remove_entry(key)
            
            # 驱逐条目以腾出空间
            self._evict_if_needed(size)
            
            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or self.default_ttl,
                size=size
            )
            
            self._cache[key] = entry
            self._current_memory += size
            self.stats['total_size'] += 1
            
            return True
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            hit_rate = 0.0
            total_requests = self.stats['hits'] + self.stats['misses']
            if total_requests > 0:
                hit_rate = self.stats['hits'] / total_requests
            
            return {
                **self.stats,
                'hit_rate': hit_rate,
                'current_size': len(self._cache),
                'current_memory': self._current_memory,
                'memory_usage_percent': (self._current_memory / self.max_memory) * 100
            }


class FileCache:
    """文件缓存"""
    
    def __init__(self, cache_dir: str = "./cache", max_files: int = 1000,
                 default_ttl: Optional[float] = None):
        """
        初始化文件缓存
        
        Args:
            cache_dir: 缓存目录
            max_files: 最大文件数
            default_ttl: 默认TTL（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_files = max_files
        self.default_ttl = default_ttl
        
        self._lock = threading.RLock()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'deletes': 0
        }
    
    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用MD5哈希避免文件名问题
        hash_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{hash_key}.cache"
    
    def _get_meta_path(self, key: str) -> Path:
        """获取元数据文件路径"""
        hash_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{hash_key}.meta"
    
    def _is_expired(self, meta_path: Path) -> bool:
        """检查文件是否过期"""
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            ttl = meta.get('ttl')
            if ttl is None:
                return False
            
            created_at = meta.get('created_at', 0)
            return time.time() - created_at > ttl
        
        except Exception:
            return True
    
    def _cleanup_old_files(self):
        """清理旧文件"""
        cache_files = list(self.cache_dir.glob("*.cache"))
        
        if len(cache_files) <= self.max_files:
            return
        
        # 按修改时间排序，删除最旧的文件
        cache_files.sort(key=lambda x: x.stat().st_mtime)
        
        files_to_delete = cache_files[:len(cache_files) - self.max_files + 1]
        
        for cache_file in files_to_delete:
            try:
                cache_file.unlink()
                # 同时删除元数据文件
                meta_file = cache_file.with_suffix('.meta')
                if meta_file.exists():
                    meta_file.unlink()
            except Exception as e:
                self.logger.error(f"删除缓存文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        with self._lock:
            file_path = self._get_file_path(key)
            meta_path = self._get_meta_path(key)
            
            if not file_path.exists() or not meta_path.exists():
                self.stats['misses'] += 1
                return default
            
            # 检查是否过期
            if self._is_expired(meta_path):
                try:
                    file_path.unlink()
                    meta_path.unlink()
                except Exception:
                    pass
                self.stats['misses'] += 1
                return default
            
            try:
                # 读取数据
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                # 更新访问时间
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                meta['accessed_at'] = time.time()
                meta['access_count'] = meta.get('access_count', 0) + 1
                
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f)
                
                self.stats['hits'] += 1
                return data
            
            except Exception as e:
                self.logger.error(f"读取缓存文件失败: {e}")
                self.stats['misses'] += 1
                return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        with self._lock:
            try:
                # 清理旧文件
                self._cleanup_old_files()
                
                file_path = self._get_file_path(key)
                meta_path = self._get_meta_path(key)
                
                # 写入数据
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
                
                # 写入元数据
                meta = {
                    'key': key,
                    'created_at': time.time(),
                    'accessed_at': time.time(),
                    'access_count': 0,
                    'ttl': ttl or self.default_ttl,
                    'size': file_path.stat().st_size
                }
                
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f)
                
                self.stats['writes'] += 1
                return True
            
            except Exception as e:
                self.logger.error(f"写入缓存文件失败: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            file_path = self._get_file_path(key)
            meta_path = self._get_meta_path(key)
            
            deleted = False
            
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted = True
                
                if meta_path.exists():
                    meta_path.unlink()
                    deleted = True
                
                if deleted:
                    self.stats['deletes'] += 1
                
                return deleted
            
            except Exception as e:
                self.logger.error(f"删除缓存文件失败: {e}")
                return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            try:
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
                
                for file_path in self.cache_dir.glob("*.meta"):
                    file_path.unlink()
                
            except Exception as e:
                self.logger.error(f"清空缓存失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            hit_rate = 0.0
            total_requests = self.stats['hits'] + self.stats['misses']
            if total_requests > 0:
                hit_rate = self.stats['hits'] / total_requests
            
            # 计算缓存文件数和总大小
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                **self.stats,
                'hit_rate': hit_rate,
                'file_count': len(cache_files),
                'total_size': total_size
            }


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化不同类型的缓存
        self.memory_cache = MemoryCache(
            max_size=self.config.get('memory_max_size', 1000),
            max_memory=self.config.get('memory_max_memory', 100 * 1024 * 1024),
            default_ttl=self.config.get('memory_default_ttl', 3600)
        )
        
        self.file_cache = FileCache(
            cache_dir=self.config.get('file_cache_dir', './cache'),
            max_files=self.config.get('file_max_files', 1000),
            default_ttl=self.config.get('file_default_ttl', 24 * 3600)
        )
        
        # 专用缓存
        self.analysis_cache = MemoryCache(
            max_size=self.config.get('analysis_max_size', 500),
            default_ttl=self.config.get('analysis_ttl', 1800)  # 30分钟
        )
        
        self.session_cache = MemoryCache(
            max_size=self.config.get('session_max_size', 100),
            default_ttl=self.config.get('session_ttl', 7200)  # 2小时
        )
        
        # 缓存键前缀
        self.prefixes = {
            'analysis': 'analysis:',
            'session': 'session:',
            'user': 'user:',
            'config': 'config:'
        }
    
    def _get_cache_key(self, cache_type: str, key: str) -> str:
        """生成缓存键"""
        prefix = self.prefixes.get(cache_type, '')
        return f"{prefix}{key}"
    
    def get(self, key: str, cache_type: str = 'memory', default: Any = None) -> Any:
        """获取缓存值"""
        cache_key = self._get_cache_key(cache_type, key)
        
        if cache_type == 'memory':
            return self.memory_cache.get(cache_key, default)
        elif cache_type == 'file':
            return self.file_cache.get(cache_key, default)
        elif cache_type == 'analysis':
            return self.analysis_cache.get(cache_key, default)
        elif cache_type == 'session':
            return self.session_cache.get(cache_key, default)
        else:
            self.logger.warning(f"未知的缓存类型: {cache_type}")
            return default
    
    def set(self, key: str, value: Any, cache_type: str = 'memory', 
           ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        cache_key = self._get_cache_key(cache_type, key)
        
        if cache_type == 'memory':
            return self.memory_cache.set(cache_key, value, ttl)
        elif cache_type == 'file':
            return self.file_cache.set(cache_key, value, ttl)
        elif cache_type == 'analysis':
            return self.analysis_cache.set(cache_key, value, ttl)
        elif cache_type == 'session':
            return self.session_cache.set(cache_key, value, ttl)
        else:
            self.logger.warning(f"未知的缓存类型: {cache_type}")
            return False
    
    def delete(self, key: str, cache_type: str = 'memory') -> bool:
        """删除缓存条目"""
        cache_key = self._get_cache_key(cache_type, key)
        
        if cache_type == 'memory':
            return self.memory_cache.delete(cache_key)
        elif cache_type == 'file':
            return self.file_cache.delete(cache_key)
        elif cache_type == 'analysis':
            return self.analysis_cache.delete(cache_key)
        elif cache_type == 'session':
            return self.session_cache.delete(cache_key)
        else:
            self.logger.warning(f"未知的缓存类型: {cache_type}")
            return False
    
    def clear(self, cache_type: Optional[str] = None):
        """清空缓存"""
        if cache_type is None:
            # 清空所有缓存
            self.memory_cache.clear()
            self.file_cache.clear()
            self.analysis_cache.clear()
            self.session_cache.clear()
        elif cache_type == 'memory':
            self.memory_cache.clear()
        elif cache_type == 'file':
            self.file_cache.clear()
        elif cache_type == 'analysis':
            self.analysis_cache.clear()
        elif cache_type == 'session':
            self.session_cache.clear()
        else:
            self.logger.warning(f"未知的缓存类型: {cache_type}")
    
    def get_analysis_result(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """获取分析结果缓存"""
        return self.get(content_hash, 'analysis')
    
    def cache_analysis_result(self, content_hash: str, result: Dict[str, Any], 
                            ttl: Optional[float] = None) -> bool:
        """缓存分析结果"""
        return self.set(content_hash, result, 'analysis', ttl)
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态缓存"""
        return self.get(session_id, 'session')
    
    def cache_session_state(self, session_id: str, state: Dict[str, Any],
                          ttl: Optional[float] = None) -> bool:
        """缓存会话状态"""
        return self.set(session_id, state, 'session', ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有缓存统计信息"""
        return {
            'memory_cache': self.memory_cache.get_stats(),
            'file_cache': self.file_cache.get_stats(),
            'analysis_cache': self.analysis_cache.get_stats(),
            'session_cache': self.session_cache.get_stats()
        }
    
    def optimize(self):
        """优化缓存性能"""
        # 这里可以实现缓存优化逻辑
        # 例如：预热常用数据、调整缓存策略等
        self.logger.info("缓存优化完成")


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def init_cache(config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """初始化缓存系统"""
    global _cache_manager
    _cache_manager = CacheManager(config)
    return _cache_manager