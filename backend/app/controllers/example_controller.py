"""
Example Controller - Controlador para generar ejemplos con IA
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.sync_session import SyncSession
from app.models.instance import Instance
from app.models.class_model import Class
from app.models.ai_generated import AIGenerated, ContentType
from app.database import get_db
from app.services.gemini_service import generate_example_options, enhance_example
from app.services.slide_generator import create_example_slide, insert_slide_in_presentation, extract_text_from_slides
from datetime import datetime
import uuid


# Almacenar solicitudes de ejemplos pendientes
pending_example_requests = {}  # request_id -> {sync_code, topic, options, timestamp}


def get_pending_request(request_id: str, db: Session):
    """
    Busca una solicitud pendiente primero en memoria, luego en la base de datos
    Retorna: (req_data, sync_session) o (None, None) si no se encuentra
    """
    # Primero buscar en memoria
    if request_id in pending_example_requests:
        req_data = pending_example_requests[request_id]
        sync_code = req_data['sync_code']

        # Buscar sesión
        sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        return (req_data, sync_session)

    # Si no está en memoria, buscar en la base de datos
    # Buscar en todas las sesiones activas que tengan pending_data con este request_id
    sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
        SyncSession.is_active == True,
        SyncSession.pending_data.isnot(None)
    ).all()

    for session in sync_session:
        if session.pending_data and 'example_request' in session.pending_data:
            example_req = session.pending_data['example_request']
            if example_req.get('request_id') == request_id:
                # Encontrado en la BD
                return (example_req, session)

    return (None, None)


def request_example(sync_code: str):
    """
    POST /api/sync/<sync_code>/example/request
    Solicita generar opciones de ejemplos
    Body: {topic: str, context: str (optional)}
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        topic = data.get('topic')

        if not topic:
            return jsonify({'error': 'Tema requerido'}), 400

        # Buscar sesión de sincronización
        sync_session = db.query(SyncSession).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Verificar si la instancia está activa
        if sync_session.instance and sync_session.instance.end_time is not None:
            return jsonify({'error': 'La clase ya ha finalizado'}), 400

        # Obtener contexto y presentación
        instance = sync_session.instance
        class_info = instance.class_ref if instance else None
        context = f"Materia: {class_info.subject}, Nivel: {class_info.level}" if class_info else ""

        # Obtener la presentación y extraer texto hasta la diapositiva actual
        pptx_path = class_info.file_path if class_info else None
        current_slide = sync_session.current_slide

        # Extraer texto solo de las últimas 3 diapositivas para evitar timeout
        slide_content = ""
        if pptx_path:
            from_slide = max(1, current_slide - 2)  # Últimas 3 slides máximo
            slide_content = extract_text_from_slides(
                pptx_path,
                from_slide=from_slide,
                up_to_slide=current_slide
            )
            # Limitar contenido a 1500 caracteres para evitar timeout
            if len(slide_content) > 1500:
                slide_content = slide_content[-1500:]
            print(f"[DEBUG] Extracted slide content ({len(slide_content)} chars) from slides {from_slide}-{current_slide}")
        else:
            print("[DEBUG] No pptx_path available")

        # Generar opciones con IA (ahora con contenido de slides limitado)
        print(f"[DEBUG] Generating examples with topic='{topic}', slide_content_len={len(slide_content)}, context='{context}'")
        options = generate_example_options(topic, slide_content, context, num_options=3)

        # Crear ID de solicitud
        request_id = str(uuid.uuid4())[:8]

        # Guardar solicitud pendiente
        pending_example_requests[request_id] = {
            'sync_code': sync_code,
            'topic': topic,
            'context': context,
            'options': options,
            'timestamp': datetime.utcnow(),
            'current_slide': sync_session.current_slide
        }

        return jsonify({
            'request_id': request_id,
            'topic': topic,
            'options': options
        }), 200

    except Exception as e:
        print(f"Error en request_example: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def select_example(request_id: str):
    """
    POST /api/example/<request_id>/select
    Selecciona una opción y genera la diapositiva
    Body: {option_index: int} (0, 1, o 2)
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        option_index = data.get('option_index')

        if option_index is None or option_index not in [0, 1, 2]:
            return jsonify({'error': 'Índice de opción inválido (debe ser 0, 1 o 2)'}), 400

        # Buscar solicitud pendiente (en memoria o BD)
        req_data, sync_session = get_pending_request(request_id, db)

        if not req_data or not sync_session:
            return jsonify({'error': 'Solicitud no encontrada o expirada'}), 404

        sync_code = req_data.get('sync_code', sync_session.sync_code)
        topic = req_data['topic']
        selected_example = req_data['options'][option_index]
        current_slide = req_data.get('current_slide', sync_session.current_slide)

        # Mejorar ejemplo con IA
        enhanced = enhance_example(selected_example, topic)

        # Obtener la presentación
        instance = sync_session.instance
        class_obj = instance.class_ref
        pptx_path = class_obj.file_path  # Usar file_path que tiene la ruta completa

        # Insertar diapositiva en la presentación
        new_slide_index = insert_slide_in_presentation(
            pptx_path=pptx_path,
            slide_data=enhanced,
            position=current_slide  # Insertar después de la diapositiva actual
        )

        # Actualizar slides_count en la clase
        class_obj.slides_count += 1

        # Regenerar imágenes de las diapositivas (no crítico - puede fallar)
        conversion_success = False
        try:
            from app.services.presentation_service import converter
            conversion_result = converter.convert_presentation(class_obj.id, pptx_path)

            if conversion_result['success']:
                class_obj.slide_urls = conversion_result['slide_urls']
                class_obj.slides_count = conversion_result['total_slides']
                conversion_success = True
        except Exception as conv_error:
            # No fallar si solo falla la conversión de imágenes
            print(f"[WARNING] Error en conversión de imágenes (no crítico): {conv_error}")
            import traceback
            traceback.print_exc()

        # Guardar registro de contenido generado por IA
        ai_content = AIGenerated(
            instance_id=instance.id,
            content_type=ContentType.EXAMPLE,
            slide_number=new_slide_index,
            prompt=topic,
            options=req_data['options'],
            selected_option=option_index,
            timestamp=datetime.utcnow()
        )
        db.add(ai_content)

        db.commit()
        db.refresh(class_obj)

        # Eliminar solicitud pendiente
        if request_id in pending_example_requests:
            del pending_example_requests[request_id]

        return jsonify({
            'message': 'Ejemplo generado exitosamente',
            'new_slide_index': new_slide_index,
            'total_slides': class_obj.slides_count,
            'slide_urls': class_obj.slide_urls,
            'conversion_success': conversion_success
        }), 200

    except Exception as e:
        db.rollback()
        error_msg = str(e) if str(e) else type(e).__name__
        print(f"Error en select_example: {error_msg}")
        import traceback
        traceback.print_exc()

        # Si el error es solo un hash/ID, usar un mensaje más descriptivo
        if len(error_msg) <= 10 and not ' ' in error_msg:
            error_msg = f"Error al generar la diapositiva. Verifica los logs para más detalles."

        return jsonify({'error': error_msg}), 500
    finally:
        db.close()


def cancel_example_request(request_id: str):
    """
    POST /api/example/<request_id>/cancel
    Cancela una solicitud de ejemplo
    """
    try:
        if request_id not in pending_example_requests:
            return jsonify({'error': 'Solicitud no encontrada'}), 404

        del pending_example_requests[request_id]

        return jsonify({'message': 'Solicitud cancelada'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def regenerate_example_options(request_id: str):
    """
    POST /api/example/<request_id>/regenerate
    Regenera nuevas opciones para una solicitud existente
    """
    db: Session = next(get_db())

    try:
        # Buscar solicitud pendiente (en memoria o BD)
        req_data, sync_session = get_pending_request(request_id, db)

        if not req_data or not sync_session:
            return jsonify({'error': 'Solicitud no encontrada'}), 404

        topic = req_data['topic']
        context = req_data.get('context', '')
        sync_code = req_data.get('sync_code', sync_session.sync_code)
        current_slide = req_data.get('current_slide', sync_session.current_slide)

        # Obtener la presentación y extraer texto
        instance = sync_session.instance
        class_obj = instance.class_ref
        pptx_path = class_obj.file_path

        # Extraer texto de las diapositivas hasta la actual
        slide_content = extract_text_from_slides(pptx_path, up_to_slide=current_slide)

        # Generar nuevas opciones con contenido de slides
        new_options = generate_example_options(topic, slide_content, context, num_options=3)

        # Actualizar opciones en memoria si existe
        if request_id in pending_example_requests:
            req_data['options'] = new_options
            req_data['timestamp'] = datetime.utcnow()

        # Actualizar opciones en BD
        if sync_session.pending_data and 'example_request' in sync_session.pending_data:
            pending_copy = dict(sync_session.pending_data)
            pending_copy['example_request']['options'] = new_options
            sync_session.pending_data = pending_copy
            db.commit()

        return jsonify({
            'request_id': request_id,
            'topic': topic,
            'options': new_options
        }), 200

    except Exception as e:
        print(f"Error en regenerate_example_options: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
