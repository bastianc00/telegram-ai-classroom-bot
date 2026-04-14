"""
Socket Emitter - Utilidad para emitir eventos WebSocket desde procesos externos (Telegram bot)
"""
import os
import socketio

# Cliente SocketIO para conectarse al servidor
sio = socketio.Client()
BACKEND_URL = os.getenv('API_BASE_URL', 'http://backend:5000')
is_connected = False


def connect_to_backend():
    """Conectar al servidor SocketIO del backend"""
    global is_connected
    if is_connected:
        return True

    try:
        print(f"[SocketIO Client] Conectando a {BACKEND_URL}...")
        sio.connect(BACKEND_URL, transports=['websocket', 'polling'])
        is_connected = True
        print("[SocketIO Client] Conectado exitosamente")
        return True
    except Exception as e:
        print(f"[SocketIO Client] Error al conectar: {e}")
        is_connected = False
        return False


def disconnect_from_backend():
    """Desconectar del servidor SocketIO"""
    global is_connected
    if is_connected:
        try:
            sio.disconnect()
            is_connected = False
            print("[SocketIO Client] Desconectado")
        except Exception as e:
            print(f"[SocketIO Client] Error al desconectar: {e}")


def emit_to_room(room, event, data):
    """
    Emitir evento a una sala específica
    Nota: Esta función hace una llamada HTTP al backend porque los clientes
    SocketIO no pueden emitir a rooms directamente, solo el servidor puede hacerlo.
    """
    # En lugar de usar SocketIO client, haremos una llamada HTTP al backend
    # para que el backend emita el evento usando socket_service.py
    import requests

    try:
        # Endpoint especial en el backend para emitir eventos desde procesos externos
        response = requests.post(
            f"{BACKEND_URL}/api/internal/socket/emit",
            json={
                'room': room,
                'event': event,
                'data': data
            },
            timeout=2
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[SocketIO Client] Error emitiendo evento: {e}")
        return False


def notify_sync_update(sync_code: str):
    """
    Notificar actualización de sincronización
    Esto hará que el backend emita un evento status_update a todos los clientes
    """
    room = f"sync_{sync_code}"
    return emit_to_room(room, 'refresh_status', {'sync_code': sync_code})


def notify_slide_change(sync_code: str, slide_number: int):
    """Notificar cambio de slide"""
    room = f"sync_{sync_code}"
    return emit_to_room(room, 'slide_update', {
        'sync_code': sync_code,
        'slide_number': slide_number
    })


def notify_command(sync_code: str, command: str):
    """Notificar comando ejecutado"""
    room = f"sync_{sync_code}"
    return emit_to_room(room, 'command', {
        'sync_code': sync_code,
        'command': command
    })


# Event handlers
@sio.event
def connect():
    print('[SocketIO Client] Conectado al servidor')


@sio.event
def disconnect():
    global is_connected
    is_connected = False
    print('[SocketIO Client] Desconectado del servidor')


@sio.event
def connect_error(data):
    print(f'[SocketIO Client] Error de conexión: {data}')
