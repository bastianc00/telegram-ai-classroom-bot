"""
Auth Controller - Controlador para autenticación de usuarios
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.user import User
from app.database import get_db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Firebase es opcional
try:
    import firebase_admin
    from firebase_admin import auth, credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


def register_email(data: dict):
    """
    POST /api/auth/register
    Registra un nuevo usuario con email/password
    """
    db: Session = next(get_db())

    try:
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('display_name', '')

        # Validaciones
        if not email or not password:
            return jsonify({'error': 'Email y contraseña requeridos'}), 400

        if len(password) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400

        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({'error': 'El usuario ya existe'}), 409

        # Crear usuario
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            display_name=display_name,
            hashed_password=hashed_password,
            auth_provider='email',
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def login_email(data: dict):
    """
    POST /api/auth/login
    Login con email/password
    """
    db: Session = next(get_db())

    try:
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email y contraseña requeridos'}), 400

        # Buscar usuario
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        if not user.hashed_password:
            return jsonify({'error': 'Usuario registrado con Google'}), 400

        # Verificar contraseña
        if not check_password_hash(user.hashed_password, password):
            return jsonify({'error': 'Credenciales inválidas'}), 401

        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.commit()

        # TODO: Generar JWT token
        # token = generate_jwt_token(user.id)

        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict(),
            # 'token': token
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def verify_firebase_token(id_token: str):
    """
    Verifica token de Firebase
    Usado para login con Google
    """
    if not FIREBASE_AVAILABLE:
        return None

    try:
        # Verificar token con Firebase Admin
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return None


def login_google(data: dict):
    """
    POST /api/auth/google
    Login con Google usando Firebase
    """
    if not FIREBASE_AVAILABLE:
        return jsonify({'error': 'Firebase no está configurado. Configure las credenciales de Firebase para usar Google Auth.'}), 503

    db: Session = next(get_db())

    try:
        id_token = data.get('id_token')

        if not id_token:
            return jsonify({'error': 'Token de Firebase requerido'}), 400

        # Verificar token
        decoded_token = verify_firebase_token(id_token)

        if not decoded_token:
            return jsonify({'error': 'Token inválido'}), 401

        # Extraer información del usuario
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        display_name = decoded_token.get('name', '')

        # Buscar o crear usuario
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

        if not user:
            # Crear nuevo usuario
            user = User(
                email=email,
                display_name=display_name,
                firebase_uid=firebase_uid,
                auth_provider='google',
                is_active=True
            )
            db.add(user)

        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        # TODO: Generar JWT token
        # token = generate_jwt_token(user.id)

        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict(),
            # 'token': token
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_current_user(user_id: int):
    """
    GET /api/auth/me
    Obtiene información del usuario actual
    """
    db: Session = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify({
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def update_profile(user_id: int, data: dict):
    """
    PUT /api/auth/profile
    Actualiza el perfil del usuario
    """
    db: Session = next(get_db())

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Actualizar campos permitidos
        if 'display_name' in data:
            user.display_name = data['display_name']

        user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(user)

        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
