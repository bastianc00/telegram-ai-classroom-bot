"""
Instance Model - Modelo de instancia de clase
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Instance(Base):
    """
    Modelo de Instancia de Clase

    Representa una ejecución/dictado específico de una clase
    """
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)

    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Calculado al finalizar

    # Slide Navigation Flow - array de slides visitadas en orden
    # Ejemplo: [1, 2, 3, 2, 3, 4, 5, 4, 5, 6...]
    slide_flow = Column(JSON, default=list)

    # Tiempo en cada slide (segundos) - diccionario {slide_num: seconds}
    slide_times = Column(JSON, default=dict)

    # Sync info
    sync_code = Column(String(10), unique=True, nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_ref = relationship("Class", back_populates="instances")
    ai_generated_content = relationship("AIGenerated", back_populates="instance", cascade="all, delete-orphan")
    sync_session = relationship("SyncSession", back_populates="instance", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Instance {self.id} - Class {self.class_id}>"

    def to_dict(self, include_ai_content=False):
        """Convierte el modelo a diccionario para JSON"""
        data = {
            'id': self.id,
            'class_id': self.class_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'slide_flow': self.slide_flow or [],
            'slide_times': self.slide_times or {},
            'sync_code': self.sync_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_ai_content:
            data['ai_generated'] = [content.to_dict() for content in self.ai_generated_content]
            data['ai_generated_count'] = len(self.ai_generated_content)

        return data
