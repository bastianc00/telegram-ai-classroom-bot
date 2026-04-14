"""
Sync Controller - Controlador para sincronización con dispositivos móviles
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.sync_session import SyncSession
from app.models.instance import Instance
from app.models.class_model import Class
from app.database import get_db
from app.services.socket_service import emit_status_update, emit_slide_update, emit_command
from datetime import datetime


def pair_device(sync_code: str):
    """
    POST /api/sync/pair
    Empareja un dispositivo con una sesión de sincronización
    Solo permite una conexión activa por presentación
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        telegram_chat_id = data.get('telegram_chat_id')
        telegram_user_id = data.get('telegram_user_id')

        if not telegram_chat_id or not telegram_user_id:
            return jsonify({'error': 'Datos de Telegram requeridos'}), 400

        # Buscar sesión de sincronización CON LOCK para prevenir race conditions
        # FOR UPDATE bloquea la fila hasta que termine la transacción
        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).with_for_update().first()

        if not sync_session:
            return jsonify({'error': 'Código de sincronización inválido'}), 404

        # Verificar si la instancia ya finalizó
        instance = sync_session.instance
        is_instance_active = instance.end_time is None if instance else False

        if not is_instance_active:
            return jsonify({
                'error': 'La clase ya ha finalizado',
                'is_instance_active': False
            }), 400

        # Verificar si ya hay una conexión activa
        if sync_session.is_connected and sync_session.telegram_user_id:
            # Si es el mismo usuario intentando reconectar, permitir
            if sync_session.telegram_user_id == telegram_user_id:
                sync_session.telegram_chat_id = telegram_chat_id
                sync_session.connected_at = datetime.utcnow()
                db.commit()
                db.refresh(sync_session)

                return jsonify({
                    'message': 'Dispositivo reconectado exitosamente',
                    'sync_session': sync_session.to_dict(),
                    'is_instance_active': True
                }), 200
            else:
                # Hay otro usuario conectado
                return jsonify({
                    'error': 'Ya hay un dispositivo conectado a esta presentación. Usa /disconnect primero para liberar la conexión.',
                    'is_connected': True
                }), 403

        # Emparejar dispositivo (primera conexión o sin conexión activa)
        sync_session.telegram_chat_id = telegram_chat_id
        sync_session.telegram_user_id = telegram_user_id
        sync_session.is_connected = True
        sync_session.connected_at = datetime.utcnow()

        db.commit()
        db.refresh(sync_session)

        return jsonify({
            'message': 'Dispositivo emparejado exitosamente',
            'sync_session': sync_session.to_dict(),
            'is_instance_active': True
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def send_command(sync_code: str):
    """
    POST /api/sync/<sync_code>/command
    Envía un comando desde el control móvil
    Comandos: next, prev, pause, resume
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        command = data.get('command')

        if not command:
            return jsonify({'error': 'Comando requerido'}), 400

        # Buscar sesión de sincronización con instance y class
        sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Verificar si la instancia está finalizada
        if sync_session.instance and sync_session.instance.end_time is not None:
            return jsonify({'error': 'La clase ya ha finalizado'}), 400

        # Get total slides from class
        total_slides = sync_session.instance.class_ref.slides_count

        # Actualizar comando
        sync_session.last_command = command
        sync_session.last_command_at = datetime.utcnow()

        # Actualizar slide actual si es next/prev
        if command == 'next':
            if sync_session.current_slide < total_slides:
                sync_session.current_slide += 1
        elif command == 'prev':
            if sync_session.current_slide > 1:
                sync_session.current_slide -= 1

        db.commit()
        db.refresh(sync_session)

        # Emitir eventos WebSocket
        emit_command(sync_code, command)
        if command in ['next', 'prev']:
            emit_slide_update(sync_code, sync_session.current_slide)
        emit_status_update(sync_code)

        return jsonify({
            'message': f'Comando {command} enviado exitosamente',
            'sync_session': sync_session.to_dict(),
            'current_slide': sync_session.current_slide,
            'total_slides': total_slides
        }), 200

    except Exception as e:
        db.rollback()
        print(f"Error in send_command: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_sync_status(sync_code: str):
    """
    GET /api/sync/<sync_code>/status
    Obtiene el estado actual de una sesión de sincronización
    """
    db: Session = next(get_db())

    try:
        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Verificar si la instancia está finalizada
        instance = sync_session.instance
        is_instance_active = instance.end_time is None if instance else False

        return jsonify({
            'sync_session': sync_session.to_dict(),
            'is_connected': sync_session.is_connected,
            'is_instance_active': is_instance_active
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def update_slide(sync_code: str):
    """
    POST /api/sync/<sync_code>/slide
    Actualiza el slide actual desde el frontend
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        slide_number = data.get('slide')

        if slide_number is None:
            return jsonify({'error': 'Número de slide requerido'}), 400

        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Update current slide
        sync_session.current_slide = slide_number
        sync_session.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(sync_session)

        # Emitir eventos WebSocket
        emit_slide_update(sync_code, slide_number)
        emit_status_update(sync_code)

        return jsonify({
            'message': 'Slide actualizado exitosamente',
            'sync_session': sync_session.to_dict()
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def disconnect_device(sync_code: str):
    """
    POST /api/sync/<sync_code>/disconnect
    Desconecta un dispositivo
    """
    db: Session = next(get_db())

    try:
        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        sync_session.is_connected = False
        sync_session.telegram_chat_id = None
        sync_session.telegram_user_id = None

        db.commit()

        return jsonify({'message': 'Dispositivo desconectado exitosamente'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
