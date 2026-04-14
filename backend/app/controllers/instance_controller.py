"""
Instance Controller - Controlador para instancias de clase
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.instance import Instance
from app.models.class_model import Class
from app.models.sync_session import SyncSession
from app.database import get_db
from datetime import datetime
import random
import string


def generate_sync_code():
    """Genera un código de sincronización único"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_instance(user_id: int, class_id: int):
    """
    POST /api/classes/<id>/instances
    Inicia una nueva instancia de clase
    """
    db: Session = next(get_db())

    try:
        # Verificar que la clase exista y pertenezca al usuario
        class_obj = db.query(Class).filter(
            Class.id == class_id,
            Class.user_id == user_id
        ).first()

        if not class_obj:
            return jsonify({'error': 'Clase no encontrada'}), 404

        # Generar código de sincronización único
        sync_code = generate_sync_code()
        while db.query(Instance).filter(Instance.sync_code == sync_code).first():
            sync_code = generate_sync_code()

        # Crear instancia
        new_instance = Instance(
            class_id=class_id,
            start_time=datetime.utcnow(),
            sync_code=sync_code,
            slide_flow=[1],  # Inicia en slide 1
            slide_times={}
        )

        db.add(new_instance)
        db.flush()  # Get instance ID before committing

        # Crear sesión de sincronización
        sync_session = SyncSession(
            instance_id=new_instance.id,
            sync_code=sync_code,
            is_connected=False,
            current_slide=1
        )

        db.add(sync_session)
        db.commit()
        db.refresh(new_instance)

        return jsonify({
            'message': 'Instancia creada exitosamente',
            'instance': new_instance.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        print(f"Error creating instance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_instances(user_id: int, class_id: int):
    """
    GET /api/classes/<id>/instances
    Obtiene todas las instancias de una clase
    """
    db: Session = next(get_db())

    try:
        # Verificar que la clase exista
        class_obj = db.query(Class).filter(
            Class.id == class_id,
            Class.user_id == user_id
        ).first()

        if not class_obj:
            return jsonify({'error': 'Clase no encontrada'}), 404

        instances = db.query(Instance).filter(
            Instance.class_id == class_id
        ).order_by(Instance.start_time.desc()).all()

        return jsonify({
            'instances': [inst.to_dict() for inst in instances],
            'total': len(instances)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def get_instance_by_id(user_id: int, class_id: int, instance_id: int):
    """
    GET /api/classes/<id>/instances/<instance_id>
    Obtiene una instancia específica con todo su detalle
    """
    db: Session = next(get_db())

    try:
        instance = db.query(Instance).join(Class).filter(
            Instance.id == instance_id,
            Instance.class_id == class_id,
            Class.user_id == user_id
        ).first()

        if not instance:
            return jsonify({'error': 'Instancia no encontrada'}), 404

        return jsonify({
            'instance': instance.to_dict(include_ai_content=True)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def update_instance(user_id: int, class_id: int, instance_id: int):
    """
    PUT /api/classes/<id>/instances/<instance_id>
    Actualiza una instancia (navegación, tiempos, etc.)
    """
    db: Session = next(get_db())

    try:
        instance = db.query(Instance).join(Class).filter(
            Instance.id == instance_id,
            Instance.class_id == class_id,
            Class.user_id == user_id
        ).first()

        if not instance:
            return jsonify({'error': 'Instancia no encontrada'}), 404

        data = request.get_json()

        # Actualizar flujo de slides
        if 'slide_flow' in data:
            instance.slide_flow = data['slide_flow']

        # Actualizar tiempos de slides
        if 'slide_times' in data:
            instance.slide_times = data['slide_times']

        # Finalizar instancia
        if 'end_time' in data:
            instance.end_time = datetime.fromisoformat(data['end_time'])
            if instance.start_time:
                duration = instance.end_time - instance.start_time
                instance.duration_minutes = int(duration.total_seconds() / 60)

        instance.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(instance)

        return jsonify({
            'message': 'Instancia actualizada exitosamente',
            'instance': instance.to_dict()
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def end_instance(user_id: int, class_id: int, instance_id: int):
    """
    POST /api/classes/<id>/instances/<instance_id>/end
    Finaliza una instancia de clase
    Recibe: slide_flow (array) y slide_times (dict) del frontend
    """
    db: Session = next(get_db())

    try:
        instance = db.query(Instance).join(Class).filter(
            Instance.id == instance_id,
            Instance.class_id == class_id,
            Class.user_id == user_id
        ).first()

        if not instance:
            return jsonify({'error': 'Instancia no encontrada'}), 404

        # Obtener datos del request (slide_flow y slide_times)
        data = request.get_json() or {}

        # Actualizar flujo de slides si se envió
        if 'slide_flow' in data and data['slide_flow']:
            instance.slide_flow = data['slide_flow']

        # Actualizar tiempos de slides si se envió
        if 'slide_times' in data and data['slide_times']:
            instance.slide_times = data['slide_times']

        # Finalizar instancia
        instance.end_time = datetime.utcnow()
        if instance.start_time:
            duration = instance.end_time - instance.start_time
            # Redondear en lugar de truncar, mínimo 1 minuto
            duration_minutes = round(duration.total_seconds() / 60)
            instance.duration_minutes = max(1, duration_minutes)

        instance.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(instance)

        return jsonify({
            'message': 'Instancia finalizada exitosamente',
            'instance': instance.to_dict(include_ai_content=True)
        }), 200

    except Exception as e:
        db.rollback()
        print(f"Error ending instance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
