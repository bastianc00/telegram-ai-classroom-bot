"""
Class Model - Modelo de clase/presentación
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Class(Base):
    """
    Modelo de Clase

    Representa una clase/presentación creada por un profesor
    """
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Basic Info
    title = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    level = Column(String(100), nullable=False)  # pregrado, postgrado, etc.
    description = Column(Text, nullable=True)

    # Presentation File
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # Ruta al archivo original PPTX
    file_size = Column(Integer, nullable=True)  # Tamaño en bytes
    slides_path = Column(String(512), nullable=True)  # Ruta a las imágenes convertidas
    slides_count = Column(Integer, default=0)
    slide_urls = Column(JSON, nullable=True)  # URLs de las slides convertidas

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="classes")
    instances = relationship("Instance", back_populates="class_ref", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Class {self.title}>"

    def to_dict(self, include_instances=False):
        """Convierte el modelo a diccionario para JSON"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'subject': self.subject,
            'level': self.level,
            'description': self.description,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'slides_count': self.slides_count,
            'slide_urls': self.slide_urls or [],
            'instance_count': len(self.instances),  # Siempre incluir el contador
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_instances:
            data['instances'] = [inst.to_dict() for inst in self.instances]

        return data
