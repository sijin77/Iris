"""
Интегрированный корректор профиля с персистентным хранилищем.
Расширяет базовый ProfileCorrector возможностями сохранения в БД.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from .profile_corrector import ProfileCorrector
from .models import FeedbackAnalysis, ProfileAdjustment, EmotionalMemoryConfig
from ..profile_persistence import get_profile_persistence_service

logger = logging.getLogger(__name__)


class IntegratedProfileCorrector(ProfileCorrector):
    """
    Расширенный корректор профиля с персистентным хранилищем.
    
    Дополнительные возможности:
    - Сохранение изменений в БД
    - Загрузка истории корректировок
    - Создание резервных копий профилей
    - Анализ эволюции профиля
    """
    
    def __init__(self, config: Optional[EmotionalMemoryConfig] = None):
        super().__init__(config)
        
        # Сервис персистентности
        self.persistence_service = get_profile_persistence_service()
        
        # Расширенная статистика
        self.stats.update({
            "adjustments_persisted": 0,
            "backups_created": 0,
            "history_loads": 0
        })
        
        logger.info("IntegratedProfileCorrector initialized with persistence")
    
    async def process_feedback_with_persistence(self, user_id: str, feedback_text: str,
                                              conversation_context: List[str] = None,
                                              agent_name: str = "iriska") -> Dict[str, Any]:
        """
        Обрабатывает обратную связь с сохранением в персистентное хранилище
        
        Args:
            user_id: ID пользователя
            feedback_text: Текст обратной связи
            conversation_context: Контекст разговора
            agent_name: Имя агента
            
        Returns:
            Результат обработки с информацией о персистентности
        """
        try:
            # Создаем резервную копию перед изменениями
            await self.create_profile_backup(agent_name)
            
            # Базовая обработка обратной связи
            result = await self.process_feedback(user_id, feedback_text, conversation_context)
            
            # Дополняем результат информацией о персистентности
            if result.get("status") == "success" and result.get("adjustments_applied"):
                persistence_results = []
                
                for adjustment in result["adjustments_applied"]:
                    # Сохраняем каждую корректировку в БД
                    persist_result = await self._persist_adjustment(
                        agent_name, user_id, adjustment, result.get("analysis")
                    )
                    persistence_results.append(persist_result)
                    
                    if persist_result.get("success"):
                        self.stats["adjustments_persisted"] += 1
                
                result["persistence_results"] = persistence_results
                result["total_persisted"] = sum(1 for r in persistence_results if r.get("success"))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in process_feedback_with_persistence: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _persist_adjustment(self, agent_name: str, user_id: str, 
                                adjustment: ProfileAdjustment, 
                                analysis: Optional[FeedbackAnalysis]) -> Dict[str, Any]:
        """
        Сохраняет корректировку профиля в персистентное хранилище
        
        Args:
            agent_name: Имя агента
            user_id: ID пользователя
            adjustment: Объект корректировки
            analysis: Результат анализа обратной связи
            
        Returns:
            Результат сохранения
        """
        try:
            # Подготавливаем данные для сохранения
            emotion_detected = None
            emotion_intensity = 0.0
            feedback_text = None
            
            if analysis:
                emotion_detected = analysis.emotion_type.value if analysis.emotion_type else None
                emotion_intensity = analysis.emotion_intensity
                feedback_text = analysis.feedback_text
            
            # Сохраняем изменение в БД
            change = await self.persistence_service.save_profile_change(
                agent_name=agent_name,
                user_id=user_id,
                field_name=adjustment.parameter_name,
                old_value=adjustment.old_value,
                new_value=adjustment.new_value,
                change_reason="emotional_feedback",
                feedback_text=feedback_text,
                confidence_score=adjustment.confidence_score,
                emotion_detected=emotion_detected,
                emotion_intensity=emotion_intensity,
                auto_apply=adjustment.confidence_score >= self.config.profile_adjustment_threshold
            )
            
            if change:
                # Если уверенность высокая, применяем изменение
                if adjustment.confidence_score >= self.config.profile_adjustment_threshold:
                    apply_success = await self.persistence_service.apply_profile_change(change.id)
                    
                    return {
                        "success": True,
                        "change_id": change.id,
                        "applied": apply_success,
                        "confidence": adjustment.confidence_score,
                        "parameter": adjustment.parameter_name
                    }
                else:
                    return {
                        "success": True,
                        "change_id": change.id,
                        "applied": False,
                        "confidence": adjustment.confidence_score,
                        "parameter": adjustment.parameter_name,
                        "reason": "low_confidence"
                    }
            else:
                return {
                    "success": False,
                    "error": "failed_to_save_change",
                    "parameter": adjustment.parameter_name
                }
                
        except Exception as e:
            logger.error(f"Error persisting adjustment: {e}")
            return {
                "success": False,
                "error": str(e),
                "parameter": adjustment.parameter_name if adjustment else "unknown"
            }
    
    async def load_adjustment_history(self, user_id: str, agent_name: str = "iriska", 
                                    days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Загружает историю корректировок для пользователя из БД
        
        Args:
            user_id: ID пользователя
            agent_name: Имя агента
            days_back: Количество дней назад
            
        Returns:
            Список исторических корректировок
        """
        try:
            changes = await self.persistence_service.get_profile_change_history(
                agent_name=agent_name,
                user_id=user_id,
                days_back=days_back,
                limit=50
            )
            
            history = []
            for change in changes:
                history.append({
                    "id": change.id,
                    "parameter_name": change.field_name,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "confidence_score": change.confidence_score,
                    "emotion_detected": change.emotion_detected,
                    "emotion_intensity": change.emotion_intensity,
                    "feedback_text": change.feedback_text,
                    "created_at": change.created_at.isoformat(),
                    "status": change.status,
                    "auto_applied": change.auto_applied,
                    "change_reason": change.change_reason
                })
            
            self.stats["history_loads"] += 1
            
            logger.info(f"Loaded {len(history)} historical adjustments for {user_id}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error loading adjustment history: {e}")
            return []
    
    async def create_profile_backup(self, agent_name: str = "iriska") -> bool:
        """
        Создает резервную копию профиля перед массовыми изменениями
        
        Args:
            agent_name: Имя агента
            
        Returns:
            True если резервная копия создана
        """
        try:
            snapshot = await self.persistence_service.create_profile_snapshot(
                agent_name=agent_name,
                snapshot_type="emotional_correction",
                trigger_event="profile_correction_backup",
                description="Backup before emotional profile corrections"
            )
            
            if snapshot:
                self.stats["backups_created"] += 1
                logger.info(f"Profile backup created for {agent_name}: snapshot {snapshot.id}")
                return True
            else:
                logger.warning(f"Failed to create profile backup for {agent_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating profile backup: {e}")
            return False
    
    async def analyze_profile_evolution(self, agent_name: str = "iriska", 
                                      days_back: int = 30) -> Dict[str, Any]:
        """
        Анализирует эволюцию профиля за указанный период
        
        Args:
            agent_name: Имя агента
            days_back: Период анализа в днях
            
        Returns:
            Результаты анализа эволюции
        """
        try:
            evolution_data = await self.persistence_service.analyze_profile_evolution(
                agent_name, days_back
            )
            
            # Добавляем анализ эффективности корректировок
            if evolution_data.get("total_changes", 0) > 0:
                evolution_data["effectiveness_analysis"] = await self._analyze_correction_effectiveness(
                    agent_name, days_back
                )
            
            return evolution_data
            
        except Exception as e:
            logger.error(f"Error analyzing profile evolution: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_correction_effectiveness(self, agent_name: str, 
                                              days_back: int) -> Dict[str, Any]:
        """Анализирует эффективность корректировок"""
        try:
            # Загружаем историю изменений
            changes = await self.persistence_service.get_profile_change_history(
                agent_name=agent_name,
                days_back=days_back,
                limit=100
            )
            
            if not changes:
                return {"status": "no_data"}
            
            # Анализируем эффективность по параметрам
            parameter_effectiveness = {}
            emotion_effectiveness = {}
            
            for change in changes:
                param = change.field_name
                emotion = change.emotion_detected
                confidence = change.confidence_score
                
                # Эффективность по параметрам
                if param not in parameter_effectiveness:
                    parameter_effectiveness[param] = {
                        "total_changes": 0,
                        "avg_confidence": 0.0,
                        "high_confidence_count": 0,
                        "applied_count": 0
                    }
                
                param_data = parameter_effectiveness[param]
                param_data["total_changes"] += 1
                param_data["avg_confidence"] = (
                    (param_data["avg_confidence"] * (param_data["total_changes"] - 1) + confidence) / 
                    param_data["total_changes"]
                )
                
                if confidence >= 0.7:
                    param_data["high_confidence_count"] += 1
                
                if change.status == "applied":
                    param_data["applied_count"] += 1
                
                # Эффективность по эмоциям
                if emotion:
                    if emotion not in emotion_effectiveness:
                        emotion_effectiveness[emotion] = {
                            "total_changes": 0,
                            "avg_confidence": 0.0,
                            "success_rate": 0.0
                        }
                    
                    emotion_data = emotion_effectiveness[emotion]
                    emotion_data["total_changes"] += 1
                    emotion_data["avg_confidence"] = (
                        (emotion_data["avg_confidence"] * (emotion_data["total_changes"] - 1) + confidence) / 
                        emotion_data["total_changes"]
                    )
            
            # Рассчитываем итоговые метрики
            total_applied = sum(1 for change in changes if change.status == "applied")
            overall_success_rate = total_applied / len(changes) if changes else 0.0
            
            return {
                "status": "analyzed",
                "overall_success_rate": overall_success_rate,
                "total_changes_analyzed": len(changes),
                "parameter_effectiveness": parameter_effectiveness,
                "emotion_effectiveness": emotion_effectiveness,
                "recommendations": self._generate_effectiveness_recommendations(
                    parameter_effectiveness, emotion_effectiveness
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correction effectiveness: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_effectiveness_recommendations(self, param_eff: Dict, emotion_eff: Dict) -> List[str]:
        """Генерирует рекомендации на основе анализа эффективности"""
        recommendations = []
        
        # Анализируем параметры с низкой эффективностью
        for param, data in param_eff.items():
            success_rate = data["applied_count"] / data["total_changes"] if data["total_changes"] > 0 else 0
            if success_rate < 0.3 and data["total_changes"] >= 3:
                recommendations.append(f"Низкая эффективность корректировок параметра '{param}' ({success_rate:.1%})")
        
        # Анализируем эмоции с высокой эффективностью
        best_emotions = sorted(
            [(emotion, data["avg_confidence"]) for emotion, data in emotion_eff.items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        
        if best_emotions:
            recommendations.append(f"Наиболее эффективные эмоциональные триггеры: {', '.join([e[0] for e in best_emotions])}")
        
        # Общие рекомендации
        if not recommendations:
            recommendations.append("Система корректировок работает стабильно")
        
        return recommendations
    
    async def rollback_recent_changes(self, agent_name: str = "iriska", 
                                    hours_back: int = 24) -> Dict[str, Any]:
        """
        Откатывает недавние изменения профиля
        
        Args:
            agent_name: Имя агента
            hours_back: Количество часов назад для отката
            
        Returns:
            Результат операции отката
        """
        try:
            rollback_datetime = datetime.utcnow() - timedelta(hours=hours_back)
            
            success = await self.persistence_service.rollback_profile_changes(
                agent_name=agent_name,
                to_datetime=rollback_datetime
            )
            
            if success:
                logger.info(f"Successfully rolled back changes for {agent_name} to {hours_back} hours ago")
                return {
                    "status": "success",
                    "rollback_datetime": rollback_datetime.isoformat(),
                    "hours_back": hours_back
                }
            else:
                return {
                    "status": "failed",
                    "error": "rollback_operation_failed"
                }
                
        except Exception as e:
            logger.error(f"Error rolling back changes: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_pending_changes(self, agent_name: str = "iriska") -> List[Dict[str, Any]]:
        """
        Получает список изменений, ожидающих применения
        
        Args:
            agent_name: Имя агента
            
        Returns:
            Список ожидающих изменений
        """
        try:
            # Получаем все изменения со статусом "pending"
            all_changes = await self.persistence_service.get_profile_change_history(
                agent_name=agent_name,
                days_back=7,  # Ищем среди недавних изменений
                limit=100
            )
            
            pending_changes = []
            for change in all_changes:
                if change.status == "pending":
                    pending_changes.append({
                        "id": change.id,
                        "parameter_name": change.field_name,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "confidence_score": change.confidence_score,
                        "feedback_text": change.feedback_text,
                        "emotion_detected": change.emotion_detected,
                        "created_at": change.created_at.isoformat(),
                        "user_id": change.user_id
                    })
            
            return pending_changes
            
        except Exception as e:
            logger.error(f"Error getting pending changes: {e}")
            return []
    
    async def apply_pending_change(self, change_id: int) -> Dict[str, Any]:
        """
        Применяет ожидающее изменение
        
        Args:
            change_id: ID изменения для применения
            
        Returns:
            Результат применения
        """
        try:
            success = await self.persistence_service.apply_profile_change(change_id)
            
            if success:
                return {
                    "status": "success",
                    "change_id": change_id,
                    "applied_at": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "change_id": change_id,
                    "error": "application_failed"
                }
                
        except Exception as e:
            logger.error(f"Error applying pending change: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_integrated_stats(self) -> Dict[str, Any]:
        """Получает расширенную статистику интегрированного корректора"""
        stats = super().get_correction_stats()
        
        # Добавляем метрики персистентности
        if stats["adjustments_applied"] > 0:
            stats["persistence_rate"] = stats["adjustments_persisted"] / stats["adjustments_applied"]
        else:
            stats["persistence_rate"] = 0.0
        
        # Добавляем информацию о сервисе персистентности
        stats["persistence_service_stats"] = self.persistence_service.get_service_stats()
        
        return stats


# Глобальный экземпляр интегрированного корректора
_integrated_profile_corrector = None


def get_integrated_profile_corrector(config: Optional[EmotionalMemoryConfig] = None) -> IntegratedProfileCorrector:
    """Получает глобальный экземпляр интегрированного корректора профилей"""
    global _integrated_profile_corrector
    if _integrated_profile_corrector is None:
        _integrated_profile_corrector = IntegratedProfileCorrector(config)
    return _integrated_profile_corrector
