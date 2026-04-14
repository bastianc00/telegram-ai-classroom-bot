"""
Helper functions para manejar sesiones de Telegram en base de datos
"""
from app.database import SessionLocal
from app.models.sync_session import SyncSession


def get_sync_session_by_chat(chat_id: int):
    """Obtiene la sesión de sincronización por chat_id"""
    db = SessionLocal()
    try:
        session = db.query(SyncSession).filter(
            SyncSession.telegram_chat_id == str(chat_id),
            SyncSession.is_active == True
        ).order_by(SyncSession.connected_at.desc()).first()
        return session
    finally:
        db.close()


def get_sync_code(chat_id: int):
    """Obtiene el sync_code de un chat_id"""
    session = get_sync_session_by_chat(chat_id)
    return session.sync_code if session else None


def get_pending_data(chat_id: int, key: str):
    """Obtiene datos pendientes de la sesión"""
    db = SessionLocal()
    try:
        session = db.query(SyncSession).filter(
            SyncSession.telegram_chat_id == str(chat_id),
            SyncSession.is_active == True
        ).first()
        print(f"[DEBUG get_pending_data] chat_id={chat_id}, key={key}, session_found={session is not None}")
        if session:
            print(f"[DEBUG get_pending_data] pending_data={session.pending_data}")
            if session.pending_data:
                result = session.pending_data.get(key)
                print(f"[DEBUG get_pending_data] result={result is not None}")
                return result
        return None
    finally:
        db.close()


def set_pending_data(chat_id: int, key: str, value):
    """Guarda datos pendientes en la sesión"""
    db = SessionLocal()
    try:
        session = db.query(SyncSession).filter(
            SyncSession.telegram_chat_id == str(chat_id),
            SyncSession.is_active == True
        ).first()
        print(f"[DEBUG set_pending_data] chat_id={chat_id}, key={key}, session_found={session is not None}")
        if session:
            if not session.pending_data:
                session.pending_data = {}
            # Crear copia mutable del dict
            pending_copy = dict(session.pending_data)
            pending_copy[key] = value
            session.pending_data = pending_copy
            db.commit()
            print(f"[DEBUG set_pending_data] Data saved successfully. pending_data={session.pending_data}")
            return True
        else:
            print(f"[DEBUG set_pending_data] No active session found for chat_id={chat_id}")
        return False
    finally:
        db.close()


def delete_pending_data(chat_id: int, key: str):
    """Elimina datos pendientes de la sesión"""
    db = SessionLocal()
    try:
        session = db.query(SyncSession).filter(
            SyncSession.telegram_chat_id == str(chat_id),
            SyncSession.is_active == True
        ).first()
        if session and session.pending_data and key in session.pending_data:
            # Crear copia mutable del dict
            pending_copy = dict(session.pending_data)
            del pending_copy[key]
            session.pending_data = pending_copy
            db.commit()
            return True
        return False
    finally:
        db.close()
