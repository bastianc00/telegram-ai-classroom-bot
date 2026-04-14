"""
SyncSession Model - Modelo para sincronización con control móvil
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class SyncSession(Base):
    """
    Modelo de Sesión de Sincronización

    Gestiona la sincronización entre la plataforma web y el control móvil (Telegram)
    """
    __tablename__ = "sync_sessions"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey('instances.id', ondelete='CASCADE'), nullable=False)

    # Sync Code - código único para vincular
    sync_code = Column(String(10), unique=True, nullable=False, index=True)

    # Telegram Info
    telegram_chat_id = Column(String(100), nullable=True)
    telegram_user_id = Column(String(100), nullable=True)
    control_message_id = Column(String(100), nullable=True)  # ID del mensaje de control en Telegram

    # Connection status
    is_connected = Column(Boolean, default=False)
    connected_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_command = Column(String(50), nullable=True)  # next, prev, pause, etc.
    last_command_at = Column(DateTime, nullable=True)

    # Current state
    current_slide = Column(Integer, default=1)
    
    # Pending requests data (para /ejemplo, /pregunta, etc.)
    pending_data = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Expiración del código

    # Relationship
    instance = relationship("Instance", back_populates="sync_session")

    def __repr__(self):
        return f"<SyncSession {self.sync_code} - Instance {self.instance_id}>"

    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'sync_code': self.sync_code,
            'is_active': self.is_active,
            'is_connected': self.is_connected,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_command': self.last_command,
            'last_command_at': self.last_command_at.isoformat() if self.last_command_at else None,
            'current_slide': self.current_slide,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }
