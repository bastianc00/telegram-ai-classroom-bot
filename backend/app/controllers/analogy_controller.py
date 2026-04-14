"""
Analogy Controller - Controlador para generar analogías simples con IA
"""
from flask import request, jsonify
from sqlalchemy.orm import Session
from app.models.sync_session import SyncSession
from app.models.instance import Instance
from app.models.class_model import Class
from app.models.ai_generated import AIGenerated, ContentType
from app.database import get_db
from app.services.gemini_service import generate_analogy_options
from app.services.slide_generator import insert_slide_in_presentation, extract_text_from_slides
from datetime import datetime
import uuid


# Almacenar solicitudes de analogías pendientes
pending_analogy_requests = {}  # request_id -> {sync_code, analogies, timestamp}


def generate_analogies(sync_code: str):
    """
    POST /api/ai/analogy/generate
    Genera 2-3 analogías simples basadas en la diapositiva actual
    """
    db: Session = next(get_db())

    try:
        # Buscar sesión de sincronización
        sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Verificar si la instancia está activa
        if sync_session.instance and sync_session.instance.end_time is not None:
            return jsonify({'error': 'La clase ya ha finalizado'}), 400

        # Obtener información de la clase
        instance = sync_session.instance
        class_info = instance.class_ref if instance else None

        # Obtener la presentación y extraer texto de la diapositiva actual
        pptx_path = class_info.file_path if class_info else None
        current_slide = sync_session.current_slide

        if not pptx_path:
            return jsonify({'error': 'No se encontró la presentación'}), 400

        # Extraer texto de las últimas 3 diapositivas para evitar timeout
        from_slide = max(1, current_slide - 2)  # Últimas 3 slides máximo
        slide_content = extract_text_from_slides(
            pptx_path,
            from_slide=from_slide,
            up_to_slide=current_slide
        )
        # Limitar contenido a 1500 caracteres para evitar timeout
        if len(slide_content) > 1500:
            slide_content = slide_content[-1500:]

        print(f"[DEBUG] Extracted {len(slide_content)} chars from slides {from_slide}-{current_slide} for analogy generation")

        if not slide_content or len(slide_content.strip()) < 10:
            return jsonify({'error': 'Las diapositivas no tienen contenido suficiente para generar analogías'}), 400

        # Generar analogías con IA
        context = f"Materia: {class_info.subject}, Nivel: {class_info.level}" if class_info else ""
        analogies = generate_analogy_options(slide_content, context)

        if not analogies or len(analogies) == 0:
            return jsonify({'error': 'No se pudieron generar analogías'}), 500

        # Crear request_id
        request_id = str(uuid.uuid4())

        # Guardar solicitud pendiente (memoria + BD)
        req_data = {
            'request_id': request_id,
            'sync_code': sync_code,
            'analogies': analogies,
            'slide_number': current_slide,
            'timestamp': datetime.utcnow().isoformat()
        }

        pending_analogy_requests[request_id] = req_data

        # También guardar en BD por si se pierde la memoria
        current_pending = sync_session.pending_data or {}
        current_pending['analogy_request'] = req_data
        sync_session.pending_data = current_pending

        db.commit()

        return jsonify({
            'request_id': request_id,
            'analogies': analogies,
            'slide_number': current_slide
        }), 200

    except Exception as e:
        db.rollback()
        print(f"Error generating analogies: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def select_analogy():
    """
    POST /api/ai/analogy/select
    Genera una diapositiva con la analogía seleccionada
    Body: {request_id: str, option_index: int, sync_code: str}
    """
    db: Session = next(get_db())

    try:
        data = request.get_json()
        request_id = data.get('request_id')
        option_index = data.get('option_index')
        sync_code = data.get('sync_code')

        if request_id is None or option_index is None or sync_code is None:
            return jsonify({'error': 'request_id, option_index y sync_code son requeridos'}), 400

        # Buscar solicitud pendiente
        req_data = pending_analogy_requests.get(request_id)

        # Si no está en memoria, buscar en BD
        if not req_data:
            sync_session_temp = db.query(SyncSession).filter(
                SyncSession.sync_code == sync_code,
                SyncSession.is_active == True
            ).first()

            if sync_session_temp and sync_session_temp.pending_data:
                req_data = sync_session_temp.pending_data.get('analogy_request')

        if not req_data:
            return jsonify({'error': 'Solicitud expirada. Usa /analogia nuevamente.'}), 404

        analogies = req_data.get('analogies', [])
        if option_index >= len(analogies):
            return jsonify({'error': 'Índice de opción inválido'}), 400

        selected_analogy = analogies[option_index]

        # Buscar sesión de sincronización con instance y class
        sync_session = db.query(SyncSession).join(Instance).join(Class).filter(
            SyncSession.sync_code == sync_code,
            SyncSession.is_active == True
        ).first()

        if not sync_session:
            return jsonify({'error': 'Sesión de sincronización no encontrada'}), 404

        # Verificar si la instancia está activa
        if sync_session.instance and sync_session.instance.end_time is not None:
            return jsonify({'error': 'La clase ya ha finalizado'}), 400

        instance = sync_session.instance
        class_info = instance.class_ref
        pptx_path = class_info.file_path
        current_slide = req_data.get('slide_number', sync_session.current_slide)

        # Crear slide_data para la analogía (mismo formato que ejemplos)
        slide_data = {
            'title': f"Explicación Simple - {class_info.subject}",
            'content': selected_analogy,
            'key_points': [],
            'is_analogy': True  # Marcador para cambiar el estilo
        }

        # Insertar la diapositiva en la presentación
        new_slide_index = insert_slide_in_presentation(
            pptx_path=pptx_path,
            slide_data=slide_data,
            position=current_slide
        )

        # Actualizar slides_count
        class_info.slides_count += 1

        # Regenerar imágenes de las diapositivas (no crítico - puede fallar)
        conversion_success = False
        try:
            from app.services.presentation_service import converter
            conversion_result = converter.convert_presentation(class_info.id, pptx_path)

            if conversion_result['success']:
                class_info.slide_urls = conversion_result['slide_urls']
                class_info.slides_count = conversion_result['total_slides']
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
            prompt=f"Analogía: Explicación simple del concepto",
            options=analogies,
            selected_option=option_index,
            timestamp=datetime.utcnow()
        )

        db.add(ai_content)

        # Limpiar solicitud pendiente
        if request_id in pending_analogy_requests:
            del pending_analogy_requests[request_id]

        if sync_session.pending_data and 'analogy_request' in sync_session.pending_data:
            del sync_session.pending_data['analogy_request']
            sync_session.pending_data = sync_session.pending_data or {}

        db.commit()
        db.refresh(class_info)

        return jsonify({
            'message': 'Analogía generada exitosamente',
            'new_slide_index': new_slide_index,
            'total_slides': class_info.slides_count,
            'slide_urls': class_info.slide_urls,
            'conversion_success': conversion_success
        }), 200

    except Exception as e:
        db.rollback()
        error_msg = str(e) if str(e) else type(e).__name__
        print(f"Error selecting analogy: {error_msg}")
        import traceback
        traceback.print_exc()

        # Si el error es solo un hash/ID, usar un mensaje más descriptivo
        if len(error_msg) <= 10 and not ' ' in error_msg:
            error_msg = f"Error al generar la analogía. Verifica los logs para más detalles."

        return jsonify({'error': error_msg}), 500
    finally:
        db.close()
