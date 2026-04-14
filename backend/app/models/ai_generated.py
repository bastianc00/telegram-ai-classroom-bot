"""
AIGenerated Model - Modelo para contenido generado con IA
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ContentType(enum.Enum):
    """Tipo de contenido generado"""
    EXAMPLE = "example"
    QUESTION = "question"


class QuestionType(enum.Enum):
    """Tipo de pregunta"""
    MULTIPLE_CHOICE = "multiple-choice"
    OPEN = "open"


class AIGenerated(Base):
    """
    Modelo de Contenido Generado con IA

    Almacena ejemplos y preguntas generadas durante la clase
    """
    __tablename__ = "ai_generated"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey('instances.id', ondelete='CASCADE'), nullable=False)

    # Tipo de contenido
    content_type = Column(SQLEnum(ContentType), nullable=False)

    # Metadata
    slide_number = Column(Integer, nullable=False)  # Slide donde se insertó
    prompt = Column(Text, nullable=False)  # Prompt usado para generar
    timestamp = Column(DateTime, default=datetime.utcnow)  # Momento de generación

    # Opciones generadas (siempre 3)
    options = Column(JSON, nullable=False)  # Lista de 3 opciones generadas
    selected_option = Column(Integer, nullable=True)  # Índice de la opción seleccionada (0-2)

    # Para preguntas
    question_type = Column(SQLEnum(QuestionType), nullable=True)

    # Audio prompt (si se usó audio para el ejemplo)
    audio_path = Column(String(512), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    instance = relationship("Instance", back_populates="ai_generated_content")

    def __repr__(self):
        return f"<AIGenerated {self.content_type.value} - Instance {self.instance_id}>"

    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'content_type': self.content_type.value,
            'slide_number': self.slide_number,
            'prompt': self.prompt,
            'options': self.options or [],
            'selected_option': self.selected_option,
            'question_type': self.question_type.value if self.question_type else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
