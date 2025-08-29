"""JSON数据管理器
负责管理分析结果的JSON文件存储
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from collections import defaultdict

from ..models.data_models import DeviationAnalysisResult, ContinuousDeviationRecord
from ..utils.logger import get_logger


class JSONDataManager:
    """JSON数据管理器"""
    
    def __init__(self, data_dir: str = "data", backup_enabled: bool = True, 
                 cache_enabled: bool = True, max_cache_size: int = 1000):
        """
        初始化JSON数据管理器
        
        Args:
            data_dir: 数据存储目录
            backup_enabled: 是否启用备份
            cache_enabled: 是否启用缓存
            max_cache_size: 最大缓存大小
        """
        self.data_dir = Path(data_dir)
        self.backup_enabled = backup_enabled
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        
        # 数据文件路径
        self.analysis_results_file = self.data_dir / "analysis_results.json"
        self.deviation_records_file = self.data_dir / "deviation_records.json"
        self.user_stats_file = self.data_dir / "user_stats.json"
        
        # 缓存
        self._cache = {} if cache_enabled else None
        self._cache_lock = threading.Lock()
        
        # 日志
        self.logger = get_logger(__name__)
        
        # 初始化
        self._init_data_files()
    
    def _init_data_files(self):
        """初始化数据文件"""
        # 创建数据目录
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据文件
        for file_path in [self.analysis_results_file, self.deviation_records_file, self.user_stats_file]:
            if not file_path.exists():
                self._write_json_file(file_path, {})
                self.logger.info(f"初始化数据文件: {file_path}")
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"读取JSON文件失败 {file_path}: {e}")
            return {}
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """写入JSON文件（原子操作）"""
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子替换
            temp_file.replace(file_path)
            
            # 创建备份
            if self.backup_enabled:
                self._create_backup(file_path)
                
        except Exception as e:
            self.logger.error(f"写入JSON文件失败 {file_path}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def _create_backup(self, file_path: Path):
        """创建备份文件"""
        try:
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{file_path.stem}_{timestamp}.json"
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file)
            
            # 清理旧备份（保留最近10个）
            self._cleanup_old_backups(backup_dir, file_path.stem)
            
        except Exception as e:
            self.logger.warning(f"创建备份失败 {file_path}: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, file_stem: str, keep_count: int = 10):
        """清理旧备份文件"""
        try:
            backup_files = list(backup_dir.glob(f"{file_stem}_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                
        except Exception as e:
            self.logger.warning(f"清理备份文件失败: {e}")
    
    def _get_cache_key(self, user_id: str, date_str: str) -> str:
        """生成缓存键"""
        return f"{user_id}_{date_str}"
    
    def _update_cache(self, user_id: str, date_str: str, result: DeviationAnalysisResult):
        """更新缓存"""
        if not self.cache_enabled:
            return
            
        with self._cache_lock:
            cache_key = self._get_cache_key(user_id, date_str)
            self._cache[cache_key] = result
            
            # 限制缓存大小
            if len(self._cache) > self.max_cache_size:
                # 删除最旧的缓存项
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
    
    def _get_from_cache(self, user_id: str, date_str: str) -> Optional[DeviationAnalysisResult]:
        """从缓存获取数据"""
        if not self.cache_enabled:
            return None
            
        with self._cache_lock:
            cache_key = self._get_cache_key(user_id, date_str)
            return self._cache.get(cache_key)
    
    def save_analysis_result(self, result: DeviationAnalysisResult) -> bool:
        """保存分析结果"""
        try:
            # 读取现有数据
            data = self._read_json_file(self.analysis_results_file)
            
            # 按用户组织数据
            user_id = result.user_id
            if user_id not in data:
                data[user_id] = {}
            
            # 保存结果（同日期会被替换）
            data[user_id][result.analysis_date] = result.to_dict()
            
            # 写入文件
            self._write_json_file(self.analysis_results_file, data)
            
            # 更新缓存
            self._update_cache(user_id, result.analysis_date, result)
            
            self.logger.info(f"保存分析结果成功: {user_id} - {result.analysis_date}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")
            return False
    
    def get_user_recent_results(self, user_id: str, days: int = 3) -> List[DeviationAnalysisResult]:
        """获取用户最近N天的分析结果"""
        try:
            results = []
            
            # 生成日期列表
            today = date.today()
            date_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
            
            # 先尝试从缓存获取
            cached_results = []
            missing_dates = []
            
            for date_str in date_list:
                cached_result = self._get_from_cache(user_id, date_str)
                if cached_result:
                    cached_results.append((date_str, cached_result))
                else:
                    missing_dates.append(date_str)
            
            # 从文件读取缺失的数据
            if missing_dates:
                data = self._read_json_file(self.analysis_results_file)
                user_data = data.get(user_id, {})
                
                for date_str in missing_dates:
                    if date_str in user_data:
                        result = DeviationAnalysisResult.from_dict(user_data[date_str])
                        cached_results.append((date_str, result))
                        # 更新缓存
                        self._update_cache(user_id, date_str, result)
            
            # 按日期排序（最新的在前）
            cached_results.sort(key=lambda x: x[0], reverse=True)
            results = [result for _, result in cached_results]
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取用户最近结果失败 {user_id}: {e}")
            return []
    
    def check_continuous_deviation(self, user_id: str, threshold: int = 3) -> bool:
        """检查用户是否连续偏离"""
        try:
            # 获取最近threshold+2天的数据，确保有足够的数据进行检查
            recent_results = self.get_user_recent_results(user_id, threshold + 2)
            
            if len(recent_results) < threshold:
                return False
            
            # 检查最近N天是否都存在偏离
            return all(result.is_deviation for result in recent_results[:threshold])
            
        except Exception as e:
            self.logger.error(f"检查连续偏离失败 {user_id}: {e}")
            return False
    
    def record_continuous_deviation(self, user_id: str, deviation_dates: List[str]) -> bool:
        """记录连续偏离情况"""
        try:
            data = self._read_json_file(self.deviation_records_file)
            
            if user_id not in data:
                data[user_id] = []
            
            # 创建新的连续偏离记录
            record = ContinuousDeviationRecord(
                user_id=user_id,
                start_date=deviation_dates[0],
                deviation_count=len(deviation_dates),
                deviation_dates=deviation_dates
            )
            
            data[user_id].append(record.to_dict())
            
            # 写入文件
            self._write_json_file(self.deviation_records_file, data)
            
            self.logger.info(f"记录连续偏离: {user_id} - {deviation_dates}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录连续偏离失败: {e}")
            return False
    
    def get_recent_active_users(self, days: int = 7) -> List[str]:
        """获取最近活跃的用户列表"""
        try:
            data = self._read_json_file(self.analysis_results_file)
            active_users = set()
            
            cutoff_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            for user_id, user_data in data.items():
                for analysis_date in user_data.keys():
                    if analysis_date >= cutoff_date:
                        active_users.add(user_id)
                        break
            
            return list(active_users)
            
        except Exception as e:
            self.logger.error(f"获取活跃用户失败: {e}")
            return []
    
    def get_user_deviation_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取用户偏离统计信息"""
        try:
            recent_results = self.get_user_recent_results(user_id, days)
            
            total_analyses = len(recent_results)
            deviation_count = sum(1 for result in recent_results if result.is_deviation)
            
            stats = {
                'user_id': user_id,
                'total_analyses': total_analyses,
                'deviation_count': deviation_count,
                'deviation_rate': deviation_count / total_analyses if total_analyses > 0 else 0,
                'recent_scores': [result.score for result in recent_results[:7]],
                'average_score': sum(result.score for result in recent_results) / total_analyses if total_analyses > 0 else 0
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取用户统计失败 {user_id}: {e}")
            return {}
    
    def cleanup_old_data(self, keep_days: int = 90) -> bool:
        """清理旧数据"""
        try:
            cutoff_date = (date.today() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
            
            # 清理分析结果
            data = self._read_json_file(self.analysis_results_file)
            cleaned_data = {}
            
            for user_id, user_data in data.items():
                cleaned_user_data = {}
                for analysis_date, result_data in user_data.items():
                    if analysis_date >= cutoff_date:
                        cleaned_user_data[analysis_date] = result_data
                
                if cleaned_user_data:
                    cleaned_data[user_id] = cleaned_user_data
            
            self._write_json_file(self.analysis_results_file, cleaned_data)
            
            # 清理缓存
            if self.cache_enabled:
                with self._cache_lock:
                    self._cache.clear()
            
            self.logger.info(f"清理旧数据完成，保留 {keep_days} 天")
            return True
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return False
    
    def export_data(self, output_file: str, user_id: Optional[str] = None, 
                   start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
        """导出数据"""
        try:
            data = self._read_json_file(self.analysis_results_file)
            
            # 过滤数据
            filtered_data = {}
            
            for uid, user_data in data.items():
                if user_id and uid != user_id:
                    continue
                
                filtered_user_data = {}
                for analysis_date, result_data in user_data.items():
                    if start_date and analysis_date < start_date:
                        continue
                    if end_date and analysis_date > end_date:
                        continue
                    
                    filtered_user_data[analysis_date] = result_data
                
                if filtered_user_data:
                    filtered_data[uid] = filtered_user_data
            
            # 导出到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据导出成功: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            return False
    
    def clear_user_cache(self, user_id: Optional[str] = None):
        """清除用户缓存"""
        if not self.cache_enabled:
            return
        
        with self._cache_lock:
            if user_id:
                # 清除特定用户的缓存
                keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{user_id}_")]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                # 清除所有缓存
                self._cache.clear()