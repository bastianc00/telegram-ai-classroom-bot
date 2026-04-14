"""
User Model - Modelo de usuario para autenticación
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    Modelo de Usuario

    Gestiona la autenticación y perfil de profesores
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=True)

    # Auth method: 'google', 'email'
    auth_provider = Column(String(50), nullable=False, default='email')

    # Solo para email/password (Firebase maneja auth de Google)
    hashed_password = Column(String(255), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    classes = relationship("Class", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'auth_provider': self.auth_provider,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
