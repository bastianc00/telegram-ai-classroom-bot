"""
Socket Service - Manejo de eventos WebSocket para sincronización en tiempo real
"""
from flask import current_app
from flask_socketio import emit, join_room, leave_room
from app.models.sync_session import SyncSession
from app.database import SessionLocal


def get_socketio():
    """Obtener instancia de socketio desde app config"""
    return current_app.config.get('SOCKETIO')


def emit_sync_update(sync_code: str, event: str, data: dict):
    """
    Emitir actualización a todos los clientes conectados a una sesión de sincronización

    Args:
        sync_code: Código de sincronización
        event: Nombre del evento
        data: Datos a enviar
    """
    socketio = get_socketio()
    if socketio:
        room = f"sync_{sync_code}"
        socketio.emit(event, data, room=room, namespace='/')


def emit_status_update(sync_code: str):
    """
    Emitir actualización de estado de sincronización

    Args:
        sync_code: Código de sincronización
    """
    db = SessionLocal()
    try:
        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return

        # Preparar datos de estado
        status_data = {
            'sync_code': sync_code,
            'is_connected': sync_session.is_connected,
            'current_slide': sync_session.current_slide,
            'telegram_chat_id': sync_session.telegram_chat_id,
            'last_command': sync_session.last_command,
            'timestamp': sync_session.updated_at.isoformat() if sync_session.updated_at else None
        }

        emit_sync_update(sync_code, 'status_update', status_data)

    finally:
        db.close()


def emit_slide_update(sync_code: str, slide_number: int):
    """
    Emitir actualización de slide actual

    Args:
        sync_code: Código de sincronización
        slide_number: Número de slide actual
    """
    emit_sync_update(sync_code, 'slide_update', {
        'sync_code': sync_code,
        'slide_number': slide_number
    })


def emit_command(sync_code: str, command: str):
    """
    Emitir comando de control (next, previous, etc)

    Args:
        sync_code: Código de sincronización
        command: Comando a ejecutar
    """
    emit_sync_update(sync_code, 'command', {
        'sync_code': sync_code,
        'command': command
    })


def emit_example_update(sync_code: str, example_data: dict):
    """
    Emitir actualización de ejemplo generado

    Args:
        sync_code: Código de sincronización
        example_data: Datos del ejemplo
    """
    emit_sync_update(sync_code, 'example_update', {
        'sync_code': sync_code,
        **example_data
    })


def emit_question_update(sync_code: str, question_data: dict):
    """
    Emitir actualización de pregunta generada

    Args:
        sync_code: Código de sincronización
        question_data: Datos de la pregunta
    """
    emit_sync_update(sync_code, 'question_update', {
        'sync_code': sync_code,
        **question_data
    })


# Manejadores de eventos de Socket.IO
def register_socket_handlers(socketio):
    """Registrar manejadores de eventos de SocketIO"""

    @socketio.on('connect')
    def handle_connect():
        print('[WebSocket] Cliente conectado')
        emit('connected', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print('[WebSocket] Cliente desconectado')

    @socketio.on('join_sync')
    def handle_join_sync(data):
        """Cliente se une a una sala de sincronización"""
        sync_code = data.get('sync_code')
        if sync_code:
            room = f"sync_{sync_code}"
            join_room(room)
            print(f'[WebSocket] Cliente se unió a sala: {room}')
            emit('joined', {'sync_code': sync_code, 'room': room})

            # Enviar estado actual inmediatamente
            emit_status_update(sync_code)

    @socketio.on('leave_sync')
    def handle_leave_sync(data):
        """Cliente sale de una sala de sincronización"""
        sync_code = data.get('sync_code')
        if sync_code:
            room = f"sync_{sync_code}"
            leave_room(room)
            print(f'[WebSocket] Cliente salió de sala: {room}')
            emit('left', {'sync_code': sync_code, 'room': room})
