"""
Database Configuration - Configuración de SQLAlchemy y PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Database URL desde .env o default para desarrollo
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/pds_proyecto3"
)

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_size=10,  # Tamaño del pool de conexiones
    max_overflow=20  # Conexiones adicionales permitidas
)

# Crear SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class para los modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obtener sesión de base de datos

    Uso:
        from app.database import get_db
        db = next(get_db())

    O en FastAPI/Flask:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa la base de datos creando todas las tablas

    IMPORTANTE: Ejecutar solo una vez o cuando se agreguen nuevos modelos
    """
    from app import models  # Import models para que SQLAlchemy los registre

    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")


def drop_all_tables():
    """
    CUIDADO: Elimina todas las tablas de la base de datos

    Solo usar en desarrollo
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  Todas las tablas han sido eliminadas")
