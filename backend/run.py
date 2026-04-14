"""
Aplicación Principal - Flask Backend
Sistema de Asistencia al Profesor basado en IA
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar configuración de base de datos
from app.database import engine, Base, SessionLocal

# Importar rutas
from app.routes.api import api

# Importar modelos para crear tablas
from app.models.user import User
from app.models.class_model import Class
from app.models.instance import Instance
from app.models.ai_generated import AIGenerated
from app.models.sync_session import SyncSession


def create_app():
    """Factory para crear la aplicación Flask"""

    # Crear instancia de Flask
    app = Flask(__name__)

    # Configuración
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

    # Crear carpetas necesarias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'presentations'), exist_ok=True)

    # Configurar CORS
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000')
    origins_list = [origin.strip() for origin in cors_origins.split(',')]
    print(f"✓ CORS configurado para: {origins_list}")

    CORS(app, resources={
        r"/api/*": {
            "origins": origins_list,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Configurar SocketIO con Redis para sincronizar eventos Y rooms entre workers
    # Importante: usar redis:// (no rediss://) para cliente síncrono con threading
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    socketio = SocketIO(
        app,
        cors_allowed_origins=origins_list,
        async_mode='threading',
        message_queue=redis_url,  # Sincroniza eventos entre workers
        # NO especificar client_manager - SocketIO lo crea automáticamente desde message_queue
        logger=True,
        engineio_logger=False
    )
    print(f"✓ SocketIO configurado con Redis: {redis_url}")

    # Guardar socketio en app config para acceso global
    app.config['SOCKETIO'] = socketio

    # Registrar handlers de WebSocket
    from app.services.socket_service import register_socket_handlers
    register_socket_handlers(socketio)

    # Registrar blueprints
    app.register_blueprint(api)

    # Crear tablas en la base de datos
    with app.app_context():
        try:
            # Verificar conexión
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # Crear tablas
            Base.metadata.create_all(bind=engine)
            print("✓ Tablas de base de datos creadas/verificadas")

            # Listar tablas creadas
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"✓ Tablas disponibles: {', '.join(tables)}")

        except Exception as e:
            print(f"✗ Error con la base de datos: {e}")
            print("⚠️  La aplicación continuará pero las operaciones de BD fallarán")

    # Ruta raíz
    @app.route('/')
    def index():
        return jsonify({
            'message': 'API Sistema de Asistencia al Profesor',
            'status': 'running',
            'version': '1.0.0'
        })

    # Health check endpoint (para Render y monitoreo)
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200

    # Servir archivos estáticos (presentaciones)
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)

    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404

    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Error interno del servidor'}), 500

    # Manejador de errores 413 (archivo muy grande)
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'Archivo demasiado grande. M�ximo 50MB'}), 413

    return app, socketio


def init_firebase():
    """Inicializar Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials

        # Opción 1: Usar variables de entorno individuales (RECOMENDADO para producción)
        firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
        firebase_private_key_id = os.getenv('FIREBASE_PRIVATE_KEY_ID')
        firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        firebase_client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        firebase_client_id = os.getenv('FIREBASE_CLIENT_ID')
        firebase_client_cert_url = os.getenv('FIREBASE_CLIENT_CERT_URL')

        if all([firebase_project_id, firebase_private_key, firebase_client_email]):
            # Construir el diccionario de credenciales desde variables de entorno
            cred_dict = {
                "type": "service_account",
                "project_id": firebase_project_id,
                "private_key_id": firebase_private_key_id,
                "private_key": firebase_private_key.replace('\\n', '\n'),  # Convertir \n a saltos de línea reales
                "client_email": firebase_client_email,
                "client_id": firebase_client_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": firebase_client_cert_url,
                "universe_domain": "googleapis.com"
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✓ Firebase Admin SDK inicializado desde variables de entorno")
            return

        # Opción 2: Usar archivo JSON (para desarrollo local)
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✓ Firebase Admin SDK inicializado desde archivo JSON")
            return

        print("⚠️  Firebase credentials no encontradas. Google Auth deshabilitado.")

    except Exception as e:
        print(f"✗ Error al inicializar Firebase: {e}")


# Crear la aplicación
app, socketio = create_app()

# Inicializar Firebase
init_firebase()


if __name__ == '__main__':
    # Configuración del servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print("\n" + "="*60)
    print("= Sistema de Asistencia al Profesor - Backend")
    print("="*60)
    print(f"= Servidor: http://{host}:{port}")
    print(f"= API: http://{host}:{port}/api")
    print(f"= WebSocket: ws://{host}:{port}")
    print(f"= Health: http://{host}:{port}/api/health")
    print(f"= Modo: {'Desarrollo' if debug else 'Producción'}")
    print("="*60 + "\n")

    # Iniciar servidor con SocketIO
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
