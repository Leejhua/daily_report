"""偏离检测跟踪器
负责检测连续偏离并触发相应的处理逻辑
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..models.data_models import DeviationAnalysisResult, ContinuousDeviationRecord
from ..storage.json_data_manager import JSONDataManager
from ..utils.logger import get_logger


@dataclass
class DeviationAlert:
    """偏离预警"""
    user_id: str
    alert_type: str  # 'continuous_deviation', 'high_score', 'pattern_change'
    severity: str    # 'low', 'medium', 'high', 'critical'
    message: str
    data: Dict[str, Any]
    created_at: str


class DeviationTracker:
    """偏离检测跟踪器"""
    
    def __init__(self, data_manager: JSONDataManager, 
                 config_or_threshold=None,
                 high_score_threshold: float = 7.0,
                 pattern_change_threshold: float = 3.0):
        """
        初始化偏离跟踪器
        
        Args:
            data_manager: JSON数据管理器
            config_or_threshold: 配置字典或连续偏离阈值（天数）
            high_score_threshold: 高分预警阈值
            pattern_change_threshold: 模式变化阈值
        """
        self.data_manager = data_manager
        
        # 处理配置参数
        if isinstance(config_or_threshold, dict):
            # 如果传入的是配置字典
            config = config_or_threshold
            self.continuous_threshold = config.get('continuous_threshold', 3)
            self.high_score_threshold = config.get('high_score_threshold', 7.0)
            self.pattern_change_threshold = config.get('pattern_change_threshold', 3.0)
        elif isinstance(config_or_threshold, int):
            # 如果传入的是整数阈值
            self.continuous_threshold = config_or_threshold
            self.high_score_threshold = high_score_threshold
            self.pattern_change_threshold = pattern_change_threshold
        else:
            # 使用默认值
            self.continuous_threshold = 3
            self.high_score_threshold = high_score_threshold
            self.pattern_change_threshold = pattern_change_threshold
        
        self.logger = get_logger(__name__)
        
        # 预警记录
        self.alerts: List[DeviationAlert] = []
    
    def record_analysis_result(self, result: DeviationAnalysisResult) -> bool:
        """记录分析结果并检查偏离情况"""
        try:
            # 保存分析结果
            success = self.data_manager.save_analysis_result(result)
            if not success:
                return False
            
            # 检查各种偏离情况
            self._check_continuous_deviation(result.user_id)
            self._check_high_score_alert(result)
            self._check_pattern_change(result.user_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"记录分析结果失败: {e}")
            return False
    
    def _check_continuous_deviation(self, user_id: str) -> Optional[DeviationAlert]:
        """检查连续偏离"""
        try:
            # 获取最近的分析结果
            recent_results = self.data_manager.get_user_recent_results(
                user_id, self.continuous_threshold
            )
            
            if len(recent_results) < self.continuous_threshold:
                return None
            
            # 检查是否连续偏离
            continuous_deviation = all(
                result.is_deviation for result in recent_results[:self.continuous_threshold]
            )
            
            if continuous_deviation:
                # 检查是否已经记录过这次连续偏离
                deviation_dates = [result.analysis_date for result in recent_results[:self.continuous_threshold]]
                deviation_dates.sort()
                
                # 记录连续偏离
                self.data_manager.record_continuous_deviation(user_id, deviation_dates)
                
                # 创建预警
                alert = DeviationAlert(
                    user_id=user_id,
                    alert_type='continuous_deviation',
                    severity='high',
                    message=f"用户 {user_id} 连续 {self.continuous_threshold} 天出现偏离",
                    data={
                        'deviation_dates': deviation_dates,
                        'scores': [result.score for result in recent_results[:self.continuous_threshold]],
                        'completion_rates': [result.completion_rate for result in recent_results[:self.continuous_threshold]]
                    },
                    created_at=datetime.now().isoformat()
                )
                
                self.alerts.append(alert)
                self.logger.warning(f"检测到连续偏离: {user_id} - {deviation_dates}")
                
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"检查连续偏离失败 {user_id}: {e}")
            return None
    
    def _check_high_score_alert(self, result: DeviationAnalysisResult) -> Optional[DeviationAlert]:
        """检查高分预警"""
        try:
            if result.score >= self.high_score_threshold:
                severity = 'critical' if result.score >= 9.0 else 'high'
                
                alert = DeviationAlert(
                    user_id=result.user_id,
                    alert_type='high_score',
                    severity=severity,
                    message=f"用户 {result.user_id} 偏离分数过高: {result.score}",
                    data={
                        'score': result.score,
                        'completion_rate': result.completion_rate,
                        'analysis_date': result.analysis_date,
                        'deviation_reasons': result.deviation_reasons
                    },
                    created_at=datetime.now().isoformat()
                )
                
                self.alerts.append(alert)
                self.logger.warning(f"检测到高分预警: {result.user_id} - {result.score}")
                
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"检查高分预警失败: {e}")
            return None
    
    def _check_pattern_change(self, user_id: str) -> Optional[DeviationAlert]:
        """检查模式变化"""
        try:
            # 获取最近7天的结果
            recent_results = self.data_manager.get_user_recent_results(user_id, 7)
            
            if len(recent_results) < 5:
                return None
            
            # 计算最近3天和之前4天的平均分数
            recent_scores = [result.score for result in recent_results[:3]]
            previous_scores = [result.score for result in recent_results[3:7]]
            
            if len(previous_scores) < 3:
                return None
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            previous_avg = sum(previous_scores) / len(previous_scores)
            
            # 检查是否有显著变化
            score_change = recent_avg - previous_avg
            
            if abs(score_change) >= self.pattern_change_threshold:
                change_type = 'deterioration' if score_change > 0 else 'improvement'
                severity = 'medium' if abs(score_change) < 5.0 else 'high'
                
                alert = DeviationAlert(
                    user_id=user_id,
                    alert_type='pattern_change',
                    severity=severity,
                    message=f"用户 {user_id} 表现模式发生变化: {change_type}",
                    data={
                        'change_type': change_type,
                        'score_change': score_change,
                        'recent_avg': recent_avg,
                        'previous_avg': previous_avg,
                        'recent_scores': recent_scores,
                        'previous_scores': previous_scores
                    },
                    created_at=datetime.now().isoformat()
                )
                
                self.alerts.append(alert)
                self.logger.info(f"检测到模式变化: {user_id} - {change_type} ({score_change:.2f})")
                
                return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"检查模式变化失败 {user_id}: {e}")
            return None
    
    def get_recent_analysis_results(self, user_id: str, days: int = 3) -> List[DeviationAnalysisResult]:
        """获取用户最近的分析结果"""
        return self.data_manager.get_user_recent_results(user_id, days)
    
    def check_continuous_deviation(self, user_id: str, analysis_date: str = None) -> Dict[str, Any]:
        """检查用户是否存在连续偏离"""
        try:
            has_continuous_deviation = self.data_manager.check_continuous_deviation(user_id, self.continuous_threshold)
            
            if has_continuous_deviation:
                # 获取连续偏离的详细信息
                recent_results = self.data_manager.get_user_recent_results(user_id, self.continuous_threshold + 2)
                
                consecutive_days = 0
                deviation_scores = []
                deviation_dates = []
                
                for result in recent_results:
                    if result.is_deviation:
                        consecutive_days += 1
                        deviation_scores.append(result.score)
                        deviation_dates.append(result.analysis_date)
                    else:
                        break
                
                return {
                    'has_continuous_deviation': True,
                    'consecutive_days': consecutive_days,
                    'deviation_dates': deviation_dates[:consecutive_days],
                    'deviation_scores': deviation_scores[:consecutive_days],
                    'avg_score': sum(deviation_scores[:consecutive_days]) / consecutive_days if consecutive_days > 0 else 0
                }
            else:
                return {
                    'has_continuous_deviation': False,
                    'consecutive_days': 0
                }
                
        except Exception as e:
            self.logger.error(f"检查连续偏离失败 {user_id}: {e}")
            return {
                'has_continuous_deviation': False,
                'consecutive_days': 0,
                'error': str(e)
            }
    
    def get_users_with_continuous_deviation(self) -> List[str]:
        """获取所有存在连续偏离的用户"""
        try:
            active_users = self.data_manager.get_recent_active_users(7)
            users_with_deviation = []
            
            for user_id in active_users:
                if self.data_manager.check_continuous_deviation(user_id, self.continuous_threshold):
                    users_with_deviation.append(user_id)
            
            return users_with_deviation
            
        except Exception as e:
            self.logger.error(f"获取连续偏离用户失败: {e}")
            return []
    
    def get_all_continuous_deviations(self) -> List[Dict[str, Any]]:
        """获取所有连续偏离的详细信息"""
        try:
            users_with_deviation = self.get_users_with_continuous_deviation()
            continuous_deviations = []
            
            for user_id in users_with_deviation:
                # 获取用户最近的分析结果
                recent_results = self.data_manager.get_user_recent_results(
                    user_id, self.continuous_threshold + 2
                )
                
                if len(recent_results) >= self.continuous_threshold:
                    # 找到连续偏离的天数
                    consecutive_days = 0
                    deviation_scores = []
                    deviation_dates = []
                    
                    for result in recent_results:
                        if result.is_deviation:
                            consecutive_days += 1
                            deviation_scores.append(result.score)
                            deviation_dates.append(result.analysis_date)
                        else:
                            break
                    
                    if consecutive_days >= self.continuous_threshold:
                        avg_deviation = sum(deviation_scores) / len(deviation_scores)
                        
                        continuous_deviations.append({
                            'user': user_id,
                            'consecutive_days': consecutive_days,
                            'avg_deviation_score': avg_deviation,
                            'deviation_dates': deviation_dates[:consecutive_days],
                            'deviation_scores': deviation_scores[:consecutive_days],
                            'latest_date': deviation_dates[0] if deviation_dates else None,
                            'severity': 'high' if avg_deviation >= 7.0 else 'medium'
                        })
            
            return continuous_deviations
            
        except Exception as e:
            self.logger.error(f"获取所有连续偏离失败: {e}")
            return []
    
    def get_user_deviation_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏离摘要"""
        try:
            # 获取基础统计
            stats = self.data_manager.get_user_deviation_stats(user_id, 30)
            
            # 获取最近分析结果
            recent_results = self.get_recent_analysis_results(user_id, 7)
            
            # 检查当前状态
            has_continuous_deviation = self.data_manager.check_continuous_deviation(
                user_id, self.continuous_threshold
            )
            
            # 获取相关预警
            user_alerts = [alert for alert in self.alerts if alert.user_id == user_id]
            recent_alerts = [
                alert for alert in user_alerts 
                if (datetime.now() - datetime.fromisoformat(alert.created_at)).days <= 7
            ]
            
            summary = {
                'user_id': user_id,
                'has_continuous_deviation': has_continuous_deviation,
                'recent_results_count': len(recent_results),
                'recent_deviation_count': sum(1 for r in recent_results if r.is_deviation),
                'recent_average_score': sum(r.score for r in recent_results) / len(recent_results) if recent_results else 0,
                'recent_alerts_count': len(recent_alerts),
                'statistics': stats,
                'recent_alerts': [{
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'created_at': alert.created_at
                } for alert in recent_alerts[-5:]]  # 最近5个预警
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取用户偏离摘要失败 {user_id}: {e}")
            return {}
    
    def record_continuous_deviation_alert(self, user_id: str, deviation_dates: List[str]) -> bool:
        """记录连续偏离预警"""
        try:
            return self.data_manager.record_continuous_deviation(user_id, deviation_dates)
        except Exception as e:
            self.logger.error(f"记录连续偏离预警失败: {e}")
            return False
    
    def cleanup_old_alerts(self, keep_days: int = 30):
        """清理旧预警记录"""
        try:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            self.alerts = [
                alert for alert in self.alerts
                if datetime.fromisoformat(alert.created_at) > cutoff_time
            ]
            
            self.logger.info(f"清理旧预警记录完成，保留 {keep_days} 天")
            
        except Exception as e:
            self.logger.error(f"清理旧预警记录失败: {e}")
    
    def get_alerts_by_type(self, alert_type: str, days: int = 7) -> List[DeviationAlert]:
        """按类型获取预警"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            return [
                alert for alert in self.alerts
                if alert.alert_type == alert_type and 
                   datetime.fromisoformat(alert.created_at) > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"获取预警失败: {e}")
            return []
    
    def get_alerts_by_severity(self, severity: str, days: int = 7) -> List[DeviationAlert]:
        """按严重程度获取预警"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            return [
                alert for alert in self.alerts
                if alert.severity == severity and 
                   datetime.fromisoformat(alert.created_at) > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"获取预警失败: {e}")
            return []
    
    def cleanup_old_data(self, keep_days: int = 90) -> bool:
        """清理旧数据"""
        try:
            # 清理数据管理器中的旧数据
            success = self.data_manager.cleanup_old_data(keep_days)
            
            # 清理旧预警
            self.cleanup_old_alerts(keep_days)
            
            return success
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return False