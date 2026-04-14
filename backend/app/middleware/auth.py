from functools import wraps
from flask import request, jsonify, g
import firebase_admin
from firebase_admin import credentials, auth
import os


# Inicializar Firebase Admin SDK
def initialize_firebase():
    """Inicializa Firebase Admin SDK si no está inicializado"""
    try:
        # Verificar si ya está inicializado
        firebase_admin.get_app()
        print("Firebase ya estaba inicializado")
    except ValueError:
        # No está inicializado, inicializar ahora
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'chatbotpdsp3-firebase-adminsdk-fbsvc-93426df3b9.json')

        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"Firebase inicializado con {cred_path}")
        else:
            print(f"Archivo de credenciales no encontrado: {cred_path}")


def verify_firebase_token(id_token):
    """
    Verifica un token de Firebase y retorna informacián del usuario

    Args:
        id_token: Token de Firebase

    Returns:
        dict con informacián del usuario o None si es inválido
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture')
        }
    except Exception as e:
        print(f"Error verificando token: {e}")
        return None


def get_token_from_request():
    """
    Extrae el token de Firebase del header Authorization

    Returns:
        Token string o None
    """
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '').strip()

    return None


def require_auth(f):
    """
    Decorator para proteger rutas que requieren autenticacián

    Uso:
        @require_auth
        def mi_ruta():
            user_id = g.user_id  # ID del usuario autenticado
            firebase_uid = g.firebase_uid
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener token del request
        token = get_token_from_request()

        if not token:
            return jsonify({'error': 'No se proporcioná token de autenticacián'}), 401

        # Verificar token con Firebase
        user_data = verify_firebase_token(token)

        if not user_data:
            return jsonify({'error': 'Token inválido o expirado'}), 401

        # Buscar o crear usuario en la BD local
        from app.database import get_db
        from app.models.user import User

        db = next(get_db())

        try:
            user = db.query(User).filter(User.firebase_uid == user_data['uid']).first()

            if not user:
                # Crear usuario automáticamente en primera autenticacián
                user = User(
                    firebase_uid=user_data['uid'],
                    email=user_data.get('email'),
                    display_name=user_data.get('name')
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Nuevo usuario creado: {user.email}")

            # Guardar informacián del usuario en el contexto de Flask
            g.user_id = user.id
            g.firebase_uid = user.firebase_uid
            g.user_email = user.email
            g.user = user

        finally:
            db.close()

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    Decorator para rutas que opcionalmente pueden usar autenticacián
    Si hay token válido, se carga el usuario en g.user_id
    Si no hay token o es inválido, la ruta contináa sin autenticacián
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if token:
            user_data = verify_firebase_token(token)

            if user_data:
                from app.database import get_db
                from app.models.user import User

                db = next(get_db())

                try:
                    user = db.query(User).filter(User.firebase_uid == user_data['uid']).first()

                    if user:
                        g.user_id = user.id
                        g.firebase_uid = user.firebase_uid
                        g.user = user
                finally:
                    db.close()

        return f(*args, **kwargs)

    return decorated_function
