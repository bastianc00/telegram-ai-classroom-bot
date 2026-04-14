"""
Question Controller - Controlador para generar preguntas con IA
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.sync_session import SyncSession
from app.models.instance import Instance
from app.models.class_model import Class
from app.models.ai_generated import AIGenerated, ContentType
from app.database import get_db
from app.services.gemini_service import generate_question_options, enhance_question
from app.services.slide_generator import create_question_slide, insert_question_slide_in_presentation, extract_text_from_slides
from datetime import datetime
import uuid


# Almacenar solicitudes de preguntas pendientes
pending_question_requests = {}  # request_id -> {sync_code, question_type, options, timestamp}


def get_pending_question_request(request_id: str, db: Session):
    """
    Busca una solicitud pendiente de pregunta primero en memoria, luego en la base de datos
    Retorna: (req_data, sync_session) o (None, None) si no se encuentra
    """
    # Primero buscar en memoria
    if request_id in pending_question_requests:
        req_data = pending_question_requests[request_id]
        sync_code = req_data['sync_code']

        # Buscar sesión
        sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        return (req_data, sync_session)

    # Si no está en memoria, buscar en la base de datos
    sync_sessions = db.query(SyncSession).join(Instance).join(Class).filter(
        SyncSession.is_active == True,
        SyncSession.pending_data.isnot(None)
    ).all()

    for session in sync_sessions:
        if session.pending_data and 'question_request' in session.pending_data:
            question_req = session.pending_data['question_request']
            if question_req.get('request_id') == request_id:
                # Encontrado en la BD
                return (question_req, session)

    return (None, None)


def request_question(sync_code: str):
    """
    POST /api/sync/<sync_code>/question/request
    Solicita generar opciones de preguntas
    Body: {
        question_type: str ("multiple-choice" o "open"),
        custom_prompt: str (opcional) - Instrucciones personalizadas del profesor
    }
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        question_type = data.get('question_type', 'multiple-choice')
        custom_prompt = data.get('custom_prompt', '')

        if question_type not in ['multiple-choice', 'open']:
            return jsonify({'error': 'Tipo de pregunta inválido (debe ser "multiple-choice" o "open")'}), 400

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

        # Obtener la presentación y extraer texto hasta la diapositiva actual
        instance = sync_session.instance
        class_obj = instance.class_ref if instance else None

        if not class_obj:
            return jsonify({'error': 'No se encontró la clase asociada'}), 404

        pptx_path = class_obj.file_path
        current_slide = sync_session.current_slide

        # Extraer texto solo de las últimas 5 diapositivas para evitar timeout
        from_slide = max(1, current_slide - 4)
        slide_content = extract_text_from_slides(
            pptx_path,
            from_slide=from_slide,
            up_to_slide=current_slide
        )
        # Limitar contenido a 2000 caracteres para evitar timeout
        if len(slide_content) > 2000:
            slide_content = slide_content[-2000:]

        print(f"[DEBUG] Extracted {len(slide_content)} chars from slides {from_slide}-{current_slide} for question generation")

        # Generar opciones con IA (incluyendo prompt personalizado si existe)
        options = generate_question_options(slide_content, question_type, custom_prompt, num_options=3)

        # Crear ID de solicitud
        request_id = str(uuid.uuid4())[:8]

        # Guardar solicitud pendiente
        pending_question_requests[request_id] = {
            'sync_code': sync_code,
            'question_type': question_type,
            'custom_prompt': custom_prompt,
            'options': options,
            'timestamp': datetime.utcnow(),
            'current_slide': current_slide
        }

        return jsonify({
            'request_id': request_id,
            'question_type': question_type,
            'options': options
        }), 200

    except Exception as e:
        print(f"Error en request_question: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def select_question(request_id: str):
    """
    POST /api/question/<request_id>/select
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
        req_data, sync_session = get_pending_question_request(request_id, db)

        if not req_data or not sync_session:
            return jsonify({'error': 'Solicitud no encontrada o expirada'}), 404

        sync_code = req_data.get('sync_code', sync_session.sync_code)
        question_type = req_data['question_type']
        custom_prompt = req_data.get('custom_prompt', '')
        selected_question = req_data['options'][option_index]
        current_slide = req_data.get('current_slide', sync_session.current_slide)

        # Mejorar pregunta con IA
        enhanced = enhance_question(selected_question, question_type)

        # Obtener la presentación
        instance = sync_session.instance
        class_obj = instance.class_ref
        pptx_path = class_obj.file_path

        # Insertar diapositiva en la presentación
        new_slide_index = insert_question_slide_in_presentation(
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

        # Construir el prompt completo para el reporte
        full_prompt = f"Pregunta tipo: {question_type}"
        if custom_prompt:
            full_prompt += f" - {custom_prompt}"

        # Guardar registro de contenido generado por IA
        ai_content = AIGenerated(
            instance_id=instance.id,
            content_type=ContentType.QUESTION,
            slide_number=new_slide_index,
            prompt=full_prompt,
            options=req_data['options'],
            selected_option=option_index,
            timestamp=datetime.utcnow()
        )
        db.add(ai_content)

        db.commit()
        db.refresh(class_obj)

        # Eliminar solicitud pendiente
        if request_id in pending_question_requests:
            del pending_question_requests[request_id]

        return jsonify({
            'message': 'Pregunta generada exitosamente',
            'new_slide_index': new_slide_index,
            'total_slides': class_obj.slides_count,
            'slide_urls': class_obj.slide_urls,
            'conversion_success': conversion_success
        }), 200

    except Exception as e:
        db.rollback()
        error_msg = str(e) if str(e) else type(e).__name__
        print(f"Error en select_question: {error_msg}")
        import traceback
        traceback.print_exc()

        # Si el error es solo un hash/ID, usar un mensaje más descriptivo
        if len(error_msg) <= 10 and not ' ' in error_msg:
            error_msg = f"Error al generar la pregunta. Verifica los logs para más detalles."

        return jsonify({'error': error_msg}), 500
    finally:
        db.close()


def cancel_question_request(request_id: str):
    """
    POST /api/question/<request_id>/cancel
    Cancela una solicitud de pregunta
    """
    try:
        if request_id not in pending_question_requests:
            return jsonify({'error': 'Solicitud no encontrada'}), 404

        del pending_question_requests[request_id]

        return jsonify({'message': 'Solicitud cancelada'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def regenerate_question_options(request_id: str):
    """
    POST /api/question/<request_id>/regenerate
    Regenera nuevas opciones para una solicitud existente
    """
    db: Session = next(get_db())

    try:
        # Buscar solicitud pendiente (en memoria o BD)
        req_data, sync_session = get_pending_question_request(request_id, db)

        if not req_data or not sync_session:
            return jsonify({'error': 'Solicitud no encontrada'}), 404

        question_type = req_data['question_type']
        custom_prompt = req_data.get('custom_prompt', '')
        sync_code = req_data.get('sync_code', sync_session.sync_code)
        current_slide = req_data.get('current_slide', sync_session.current_slide)

        # Obtener la presentación y extraer texto
        instance = sync_session.instance
        class_obj = instance.class_ref
        pptx_path = class_obj.file_path

        # Extraer texto solo de las últimas 5 diapositivas para evitar timeout
        from_slide = max(1, current_slide - 4)
        slide_content = extract_text_from_slides(
            pptx_path,
            from_slide=from_slide,
            up_to_slide=current_slide
        )
        # Limitar contenido a 2000 caracteres para evitar timeout
        if len(slide_content) > 2000:
            slide_content = slide_content[-2000:]

        # Generar nuevas opciones (con custom_prompt si existe)
        new_options = generate_question_options(slide_content, question_type, custom_prompt, num_options=3)

        # Actualizar opciones en memoria si existe
        if request_id in pending_question_requests:
            req_data['options'] = new_options
            req_data['timestamp'] = datetime.utcnow()

        # Actualizar opciones en BD
        if sync_session.pending_data and 'question_request' in sync_session.pending_data:
            pending_copy = dict(sync_session.pending_data)
            pending_copy['question_request']['options'] = new_options
            sync_session.pending_data = pending_copy
            db.commit()

        return jsonify({
            'request_id': request_id,
            'question_type': question_type,
            'options': new_options
        }), 200

    except Exception as e:
        print(f"Error en regenerate_question_options: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
