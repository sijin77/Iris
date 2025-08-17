"""
Сервис персистентного хранения изменений профилей агентов.
Обеспечивает сохранение, откат и анализ изменений профилей.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .models import SessionLocal, AgentProfile
from .models_extended import (
    ProfileChange, ProfileSnapshot, FeedbackAnalysis,
    create_profile_change, create_profile_snapshot
)

logger = logging.getLogger(__name__)


class ProfilePersistenceService:
    """
    Сервис для управления персистентным хранением профилей агентов.
    
    Основные функции:
    - Сохранение изменений профилей
    - Создание снимков состояния
    - Откат изменений
    - Анализ истории изменений
    - Автоматическое резервное копирование
    """
    
    def __init__(self):
        self.stats = {
            "total_changes_saved": 0,
            "snapshots_created": 0,
            "rollbacks_performed": 0,
            "last_operation_time": None
        }
        
        logger.info("ProfilePersistenceService initialized")
    
    def get_db_session(self) -> Session:
        """Получает сессию базы данных"""
        return SessionLocal()
    
    async def save_profile_change(self, agent_name: str, user_id: str, 
                                 field_name: str, old_value: Any, new_value: Any,
                                 change_reason: str = "manual", 
                                 feedback_text: str = None,
                                 confidence_score: float = 0.0,
                                 emotion_detected: str = None,
                                 emotion_intensity: float = 0.0,
                                 auto_apply: bool = False) -> Optional[ProfileChange]:
        """
        Сохраняет изменение профиля в базе данных
        
        Args:
            agent_name: Имя агента
            user_id: ID пользователя
            field_name: Название изменяемого поля
            old_value: Старое значение
            new_value: Новое значение
            change_reason: Причина изменения
            feedback_text: Текст обратной связи
            confidence_score: Уверенность в изменении
            emotion_detected: Обнаруженная эмоция
            emotion_intensity: Интенсивность эмоции
            auto_apply: Применить автоматически
            
        Returns:
            Созданная запись ProfileChange или None при ошибке
        """
        try:
            with self.get_db_session() as db:
                # Конвертируем значения в строки для хранения
                old_value_str = json.dumps(old_value) if not isinstance(old_value, str) else old_value
                new_value_str = json.dumps(new_value) if not isinstance(new_value, str) else new_value
                
                # Создаем запись об изменении
                change = create_profile_change(
                    agent_name=agent_name,
                    user_id=user_id,
                    field_name=field_name,
                    old_value=old_value_str,
                    new_value=new_value_str,
                    change_reason=change_reason,
                    feedback_text=feedback_text,
                    confidence_score=confidence_score,
                    emotion_detected=emotion_detected,
                    emotion_intensity=emotion_intensity
                )
                
                # Устанавливаем статус
                if auto_apply:
                    change.status = "applied"
                    change.auto_applied = True
                    change.applied_at = datetime.utcnow()
                
                db.add(change)
                db.commit()
                db.refresh(change)
                
                self.stats["total_changes_saved"] += 1
                self.stats["last_operation_time"] = datetime.utcnow()
                
                logger.info(f"Profile change saved: {agent_name}.{field_name} by {user_id}")
                
                return change
                
        except Exception as e:
            logger.error(f"Error saving profile change: {e}")
            return None
    
    async def apply_profile_change(self, change_id: int) -> bool:
        """
        Применяет изменение профиля к реальному профилю агента
        
        Args:
            change_id: ID изменения для применения
            
        Returns:
            True если изменение успешно применено
        """
        try:
            with self.get_db_session() as db:
                # Получаем изменение
                change = db.query(ProfileChange).filter(ProfileChange.id == change_id).first()
                if not change:
                    logger.warning(f"Profile change {change_id} not found")
                    return False
                
                if change.status == "applied":
                    logger.info(f"Profile change {change_id} already applied")
                    return True
                
                # Получаем профиль агента
                profile = db.query(AgentProfile).filter(AgentProfile.name == change.agent_name).first()
                if not profile:
                    logger.error(f"Agent profile {change.agent_name} not found")
                    return False
                
                # Создаем снимок перед изменением
                await self.create_profile_snapshot(
                    change.agent_name, 
                    snapshot_type="pre_change",
                    trigger_event=f"change_{change_id}"
                )
                
                # Применяем изменение
                success = self._apply_field_change(profile, change.field_name, change.new_value)
                
                if success:
                    # Обновляем статус изменения
                    change.status = "applied"
                    change.applied_at = datetime.utcnow()
                    
                    db.commit()
                    
                    logger.info(f"Profile change {change_id} applied successfully")
                    return True
                else:
                    logger.error(f"Failed to apply profile change {change_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error applying profile change: {e}")
            return False
    
    def _apply_field_change(self, profile: AgentProfile, field_name: str, new_value_str: str) -> bool:
        """Применяет изменение конкретного поля профиля"""
        try:
            # Парсим новое значение
            try:
                new_value = json.loads(new_value_str)
            except (json.JSONDecodeError, TypeError):
                new_value = new_value_str
            
            # Применяем изменение в зависимости от поля
            if hasattr(profile, field_name):
                setattr(profile, field_name, new_value)
                return True
            else:
                logger.warning(f"Unknown field {field_name} for profile")
                return False
                
        except Exception as e:
            logger.error(f"Error applying field change: {e}")
            return False
    
    async def create_profile_snapshot(self, agent_name: str, 
                                    snapshot_type: str = "automatic",
                                    trigger_event: str = None,
                                    description: str = None) -> Optional[ProfileSnapshot]:
        """
        Создает снимок текущего состояния профиля
        
        Args:
            agent_name: Имя агента
            snapshot_type: Тип снимка
            trigger_event: Событие, вызвавшее создание снимка
            description: Описание снимка
            
        Returns:
            Созданный снимок или None при ошибке
        """
        try:
            with self.get_db_session() as db:
                # Получаем текущий профиль
                profile = db.query(AgentProfile).filter(AgentProfile.name == agent_name).first()
                if not profile:
                    logger.error(f"Agent profile {agent_name} not found")
                    return None
                
                # Конвертируем профиль в словарь
                profile_data = self._profile_to_dict(profile)
                
                # Получаем статистику изменений
                total_changes = db.query(func.count(ProfileChange.id)).filter(
                    ProfileChange.agent_name == agent_name
                ).scalar() or 0
                
                # Создаем снимок
                snapshot = create_profile_snapshot(
                    agent_name=agent_name,
                    profile_data=profile_data,
                    snapshot_type=snapshot_type,
                    trigger_event=trigger_event
                )
                
                snapshot.description = description
                snapshot.total_changes = total_changes
                
                db.add(snapshot)
                db.commit()
                db.refresh(snapshot)
                
                self.stats["snapshots_created"] += 1
                self.stats["last_operation_time"] = datetime.utcnow()
                
                logger.info(f"Profile snapshot created for {agent_name}: {snapshot_type}")
                
                return snapshot
                
        except Exception as e:
            logger.error(f"Error creating profile snapshot: {e}")
            return None
    
    def _profile_to_dict(self, profile: AgentProfile) -> Dict[str, Any]:
        """Конвертирует профиль агента в словарь"""
        return {
            "id": profile.id,
            "name": profile.name,
            "created_by": profile.created_by,
            "status": profile.status,
            "access_level": profile.access_level,
            "is_main_agent": profile.is_main_agent,
            "specialization": profile.specialization,
            "purpose": profile.purpose,
            "system_prompt": profile.system_prompt,
            "personality_traits": profile.personality_traits,
            "tone": profile.tone,
            "communication_style": profile.communication_style,
            "safety_rules": profile.safety_rules,
            "allowed_tools": profile.allowed_tools,
            "restricted_actions": profile.restricted_actions,
            "generation_settings": profile.generation_settings,
            "max_tokens": profile.max_tokens,
            "temperature": profile.temperature,
            "context_window": profile.context_window,
            "memory_type": profile.memory_type,
            "version": profile.version,
            "tags": profile.tags,
            "description": profile.description,
            "notes": profile.notes,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "last_activated": profile.last_activated.isoformat() if profile.last_activated else None,
            "last_used": profile.last_used.isoformat() if profile.last_used else None,
            "usage_count": profile.usage_count,
            "total_tokens_used": profile.total_tokens_used
        }
    
    async def rollback_profile_changes(self, agent_name: str, 
                                     to_snapshot_id: int = None,
                                     to_datetime: datetime = None) -> bool:
        """
        Откатывает изменения профиля к определенному состоянию
        
        Args:
            agent_name: Имя агента
            to_snapshot_id: ID снимка для отката (приоритет)
            to_datetime: Дата для отката (если snapshot_id не указан)
            
        Returns:
            True если откат успешен
        """
        try:
            with self.get_db_session() as db:
                target_snapshot = None
                
                # Ищем целевой снимок
                if to_snapshot_id:
                    target_snapshot = db.query(ProfileSnapshot).filter(
                        and_(
                            ProfileSnapshot.id == to_snapshot_id,
                            ProfileSnapshot.agent_name == agent_name
                        )
                    ).first()
                elif to_datetime:
                    target_snapshot = db.query(ProfileSnapshot).filter(
                        and_(
                            ProfileSnapshot.agent_name == agent_name,
                            ProfileSnapshot.created_at <= to_datetime
                        )
                    ).order_by(desc(ProfileSnapshot.created_at)).first()
                
                if not target_snapshot:
                    logger.error(f"Target snapshot not found for rollback")
                    return False
                
                # Получаем текущий профиль
                current_profile = db.query(AgentProfile).filter(
                    AgentProfile.name == agent_name
                ).first()
                
                if not current_profile:
                    logger.error(f"Current profile {agent_name} not found")
                    return False
                
                # Создаем снимок текущего состояния перед откатом
                await self.create_profile_snapshot(
                    agent_name,
                    snapshot_type="pre_rollback",
                    trigger_event=f"rollback_to_{target_snapshot.id}",
                    description="Backup before rollback"
                )
                
                # Восстанавливаем состояние из снимка
                success = self._restore_profile_from_snapshot(current_profile, target_snapshot.profile_data)
                
                if success:
                    db.commit()
                    
                    self.stats["rollbacks_performed"] += 1
                    self.stats["last_operation_time"] = datetime.utcnow()
                    
                    logger.info(f"Profile {agent_name} rolled back to snapshot {target_snapshot.id}")
                    return True
                else:
                    db.rollback()
                    logger.error(f"Failed to rollback profile {agent_name}")
                    return False
                
        except Exception as e:
            logger.error(f"Error during profile rollback: {e}")
            return False
    
    def _restore_profile_from_snapshot(self, profile: AgentProfile, snapshot_data: Dict[str, Any]) -> bool:
        """Восстанавливает профиль из данных снимка"""
        try:
            # Поля, которые не нужно восстанавливать (системные)
            skip_fields = {"id", "name", "created_at", "usage_count", "total_tokens_used"}
            
            for field_name, value in snapshot_data.items():
                if field_name not in skip_fields and hasattr(profile, field_name):
                    setattr(profile, field_name, value)
            
            # Обновляем временные метки
            profile.last_used = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring profile from snapshot: {e}")
            return False
    
    async def get_profile_change_history(self, agent_name: str, 
                                       user_id: str = None,
                                       days_back: int = 30,
                                       limit: int = 100) -> List[ProfileChange]:
        """
        Получает историю изменений профиля
        
        Args:
            agent_name: Имя агента
            user_id: ID пользователя (опционально)
            days_back: Количество дней назад
            limit: Максимальное количество записей
            
        Returns:
            Список изменений профиля
        """
        try:
            with self.get_db_session() as db:
                query = db.query(ProfileChange).filter(
                    ProfileChange.agent_name == agent_name
                )
                
                if user_id:
                    query = query.filter(ProfileChange.user_id == user_id)
                
                if days_back:
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                    query = query.filter(ProfileChange.created_at >= cutoff_date)
                
                changes = query.order_by(desc(ProfileChange.created_at)).limit(limit).all()
                
                return changes
                
        except Exception as e:
            logger.error(f"Error getting profile change history: {e}")
            return []
    
    async def get_profile_snapshots(self, agent_name: str, 
                                  snapshot_type: str = None,
                                  limit: int = 50) -> List[ProfileSnapshot]:
        """Получает список снимков профиля"""
        try:
            with self.get_db_session() as db:
                query = db.query(ProfileSnapshot).filter(
                    ProfileSnapshot.agent_name == agent_name
                )
                
                if snapshot_type:
                    query = query.filter(ProfileSnapshot.snapshot_type == snapshot_type)
                
                snapshots = query.order_by(desc(ProfileSnapshot.created_at)).limit(limit).all()
                
                return snapshots
                
        except Exception as e:
            logger.error(f"Error getting profile snapshots: {e}")
            return []
    
    async def analyze_profile_evolution(self, agent_name: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Анализирует эволюцию профиля за указанный период
        
        Args:
            agent_name: Имя агента
            days_back: Период анализа в днях
            
        Returns:
            Словарь с результатами анализа
        """
        try:
            with self.get_db_session() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                
                # Получаем изменения за период
                changes = db.query(ProfileChange).filter(
                    and_(
                        ProfileChange.agent_name == agent_name,
                        ProfileChange.created_at >= cutoff_date
                    )
                ).all()
                
                if not changes:
                    return {"status": "no_changes", "period_days": days_back}
                
                # Анализируем изменения
                analysis = {
                    "period_days": days_back,
                    "total_changes": len(changes),
                    "changes_by_field": {},
                    "changes_by_reason": {},
                    "changes_by_user": {},
                    "emotional_context": {},
                    "confidence_stats": {
                        "avg_confidence": 0.0,
                        "high_confidence_changes": 0,
                        "low_confidence_changes": 0
                    },
                    "timeline": []
                }
                
                total_confidence = 0.0
                emotions_detected = {}
                
                for change in changes:
                    # Группировка по полям
                    field = change.field_name
                    analysis["changes_by_field"][field] = analysis["changes_by_field"].get(field, 0) + 1
                    
                    # Группировка по причинам
                    reason = change.change_reason
                    analysis["changes_by_reason"][reason] = analysis["changes_by_reason"].get(reason, 0) + 1
                    
                    # Группировка по пользователям
                    user = change.user_id
                    analysis["changes_by_user"][user] = analysis["changes_by_user"].get(user, 0) + 1
                    
                    # Анализ уверенности
                    total_confidence += change.confidence_score
                    if change.confidence_score >= 0.7:
                        analysis["confidence_stats"]["high_confidence_changes"] += 1
                    elif change.confidence_score <= 0.3:
                        analysis["confidence_stats"]["low_confidence_changes"] += 1
                    
                    # Эмоциональный контекст
                    if change.emotion_detected:
                        emotion = change.emotion_detected
                        emotions_detected[emotion] = emotions_detected.get(emotion, 0) + 1
                    
                    # Временная линия
                    analysis["timeline"].append({
                        "date": change.created_at.isoformat(),
                        "field": change.field_name,
                        "reason": change.change_reason,
                        "user_id": change.user_id,
                        "confidence": change.confidence_score,
                        "emotion": change.emotion_detected
                    })
                
                # Финализируем статистику
                analysis["confidence_stats"]["avg_confidence"] = total_confidence / len(changes)
                analysis["emotional_context"] = emotions_detected
                
                # Сортируем временную линию
                analysis["timeline"].sort(key=lambda x: x["date"], reverse=True)
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing profile evolution: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Очищает старые данные (изменения и снимки)
        
        Args:
            days_to_keep: Сколько дней данных сохранять
            
        Returns:
            Статистика очистки
        """
        try:
            with self.get_db_session() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Удаляем старые изменения (кроме applied)
                old_changes = db.query(ProfileChange).filter(
                    and_(
                        ProfileChange.created_at < cutoff_date,
                        ProfileChange.status != "applied"
                    )
                ).delete()
                
                # Удаляем старые автоматические снимки (оставляем важные)
                old_snapshots = db.query(ProfileSnapshot).filter(
                    and_(
                        ProfileSnapshot.created_at < cutoff_date,
                        ProfileSnapshot.snapshot_type == "automatic"
                    )
                ).delete()
                
                db.commit()
                
                cleanup_stats = {
                    "changes_deleted": old_changes,
                    "snapshots_deleted": old_snapshots,
                    "cutoff_date": cutoff_date.isoformat()
                }
                
                logger.info(f"Cleanup completed: {cleanup_stats}")
                
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Получает статистику работы сервиса"""
        return self.stats.copy()


# Глобальный экземпляр сервиса
_profile_persistence_service = None


def get_profile_persistence_service() -> ProfilePersistenceService:
    """Получает глобальный экземпляр сервиса персистентности профилей"""
    global _profile_persistence_service
    if _profile_persistence_service is None:
        _profile_persistence_service = ProfilePersistenceService()
    return _profile_persistence_service
