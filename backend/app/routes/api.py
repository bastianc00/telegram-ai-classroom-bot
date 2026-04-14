"""
API Routes - Definición de todas las rutas de la aplicación
"""
from flask import Blueprint, request, g
from app.controllers import (
    class_controller,
    instance_controller,
    sync_controller,
    auth_controller,
    example_controller,
    question_controller,
    analogy_controller,
    telegram_webhook_controller
)
from app.middleware.auth import require_auth, optional_auth

# Crear blueprint
api = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# ROUTES: AUTHENTICATION
# ============================================================================

@api.route('/auth/register', methods=['POST'])
def register_route():
    """POST /api/auth/register - Registrar usuario con email/password"""
    data = request.get_json()
    return auth_controller.register_email(data)


@api.route('/auth/login', methods=['POST'])
def login_route():
    """POST /api/auth/login - Login con email/password"""
    data = request.get_json()
    return auth_controller.login_email(data)


@api.route('/auth/google', methods=['POST'])
def google_login_route():
    """POST /api/auth/google - Login con Google/Firebase"""
    data = request.get_json()
    return auth_controller.login_google(data)


@api.route('/auth/me', methods=['GET'])
@require_auth
def get_me_route():
    """GET /api/auth/me - Obtener usuario actual"""
    return auth_controller.get_current_user(g.user_id)


@api.route('/auth/profile', methods=['GET', 'PUT'])
@require_auth
def profile_route():
    """GET/PUT /api/auth/profile - Obtener o actualizar perfil de usuario"""
    if request.method == 'GET':
        return auth_controller.get_current_user(g.user_id)
    else:  # PUT
        data = request.get_json()
        return auth_controller.update_profile(g.user_id, data)


# ============================================================================
# ROUTES: CLASSES
# ============================================================================

@api.route('/classes', methods=['POST'])
@require_auth
def create_class_route():
    """POST /api/classes - Crear nueva clase"""
    return class_controller.create_class(g.user_id)


@api.route('/classes', methods=['GET'])
@require_auth
def get_classes_route():
    """GET /api/classes - Obtener todas las clases del usuario"""
    return class_controller.get_classes(g.user_id)


@api.route('/classes/<int:class_id>', methods=['GET'])
@require_auth
def get_class_route(class_id):
    """GET /api/classes/<id> - Obtener clase específica"""
    return class_controller.get_class_by_id(g.user_id, class_id)


@api.route('/classes/<int:class_id>', methods=['PUT'])
@require_auth
def update_class_route(class_id):
    """PUT /api/classes/<id> - Actualizar clase"""
    return class_controller.update_class(g.user_id, class_id)


@api.route('/classes/<int:class_id>', methods=['DELETE'])
@require_auth
def delete_class_route(class_id):
    """DELETE /api/classes/<id> - Eliminar clase"""
    return class_controller.delete_class(g.user_id, class_id)


# ============================================================================
# ROUTES: INSTANCES
# ============================================================================

@api.route('/classes/<int:class_id>/instances', methods=['POST'])
@require_auth
def create_instance_route(class_id):
    """POST /api/classes/<id>/instances - Iniciar nueva instancia"""
    return instance_controller.create_instance(g.user_id, class_id)


@api.route('/classes/<int:class_id>/instances', methods=['GET'])
@require_auth
def get_instances_route(class_id):
    """GET /api/classes/<id>/instances - Obtener instancias de una clase"""
    return instance_controller.get_instances(g.user_id, class_id)


@api.route('/classes/<int:class_id>/instances/<int:instance_id>', methods=['GET'])
@require_auth
def get_instance_route(class_id, instance_id):
    """GET /api/classes/<id>/instances/<instance_id> - Obtener instancia específica"""
    return instance_controller.get_instance_by_id(g.user_id, class_id, instance_id)


@api.route('/classes/<int:class_id>/instances/<int:instance_id>', methods=['PUT'])
@require_auth
def update_instance_route(class_id, instance_id):
    """PUT /api/classes/<id>/instances/<instance_id> - Actualizar instancia"""
    return instance_controller.update_instance(g.user_id, class_id, instance_id)


@api.route('/classes/<int:class_id>/instances/<int:instance_id>/end', methods=['POST'])
@require_auth
def end_instance_route(class_id, instance_id):
    """POST /api/classes/<id>/instances/<instance_id>/end - Finalizar instancia"""
    return instance_controller.end_instance(g.user_id, class_id, instance_id)


# ============================================================================
# ROUTES: SYNC (Sincronización con Telegram)
# ============================================================================

@api.route('/sync/pair', methods=['POST'])
def pair_device_route():
    """POST /api/sync/pair - Vincular dispositivo con código"""
    from flask import request
    sync_code = request.json.get('sync_code')
    if not sync_code:
        return {'error': 'sync_code requerido'}, 400
    return sync_controller.pair_device(sync_code)


@api.route('/sync/<string:sync_code>/command', methods=['POST'])
def send_command_route(sync_code):
    """POST /api/sync/<code>/command - Enviar comando desde control"""
    return sync_controller.send_command(sync_code)


@api.route('/sync/<string:sync_code>/status', methods=['GET'])
def get_sync_status_route(sync_code):
    """GET /api/sync/<code>/status - Obtener estado de sincronización"""
    return sync_controller.get_sync_status(sync_code)


@api.route('/sync/<string:sync_code>/slide', methods=['POST'])
def update_slide_route(sync_code):
    """POST /api/sync/<code>/slide - Actualizar slide actual desde frontend"""
    return sync_controller.update_slide(sync_code)


@api.route('/sync/<string:sync_code>/disconnect', methods=['POST'])
def disconnect_device_route(sync_code):
    """POST /api/sync/<code>/disconnect - Desconectar dispositivo"""
    return sync_controller.disconnect_device(sync_code)


# ============================================================================
# ROUTES: EXAMPLES (Generación de ejemplos con IA)
# ============================================================================

@api.route('/sync/<string:sync_code>/example/request', methods=['POST'])
def request_example_route(sync_code):
    """POST /api/sync/<code>/example/request - Solicitar generar ejemplos con IA"""
    return example_controller.request_example(sync_code)


@api.route('/example/<string:request_id>/select', methods=['POST'])
def select_example_route(request_id):
    """POST /api/example/<request_id>/select - Seleccionar ejemplo y generar diapositiva"""
    return example_controller.select_example(request_id)


@api.route('/example/<string:request_id>/cancel', methods=['POST'])
def cancel_example_route(request_id):
    """POST /api/example/<request_id>/cancel - Cancelar solicitud de ejemplo"""
    return example_controller.cancel_example_request(request_id)


@api.route('/example/<string:request_id>/regenerate', methods=['POST'])
def regenerate_example_route(request_id):
    """POST /api/example/<request_id>/regenerate - Regenerar opciones de ejemplo"""
    return example_controller.regenerate_example_options(request_id)


# ============================================================================
# ROUTES: QUESTIONS (Generación de preguntas con IA)
# ============================================================================

@api.route('/sync/<string:sync_code>/question/request', methods=['POST'])
def request_question_route(sync_code):
    """POST /api/sync/<code>/question/request - Solicitar generar preguntas con IA"""
    return question_controller.request_question(sync_code)


@api.route('/question/<string:request_id>/select', methods=['POST'])
def select_question_route(request_id):
    """POST /api/question/<request_id>/select - Seleccionar pregunta y generar diapositiva"""
    return question_controller.select_question(request_id)


@api.route('/question/<string:request_id>/cancel', methods=['POST'])
def cancel_question_route(request_id):
    """POST /api/question/<request_id>/cancel - Cancelar solicitud de pregunta"""
    return question_controller.cancel_question_request(request_id)


@api.route('/question/<string:request_id>/regenerate', methods=['POST'])
def regenerate_question_route(request_id):
    """POST /api/question/<request_id>/regenerate - Regenerar opciones de pregunta"""
    return question_controller.regenerate_question_options(request_id)


# ============================================================================
# ROUTES: AI ANALOGIES
# ============================================================================

@api.route('/ai/analogy/generate', methods=['POST'])
def generate_analogy_route():
    """POST /api/ai/analogy/generate - Generar analogías con IA"""
    data = request.get_json()
    sync_code = data.get('sync_code')
    return analogy_controller.generate_analogies(sync_code)


@api.route('/ai/analogy/select', methods=['POST'])
def select_analogy_route():
    """POST /api/ai/analogy/select - Seleccionar analogía y generar diapositiva"""
    return analogy_controller.select_analogy()


# ============================================================================
# ROUTES: TELEGRAM WEBHOOK
# ============================================================================

@api.route('/telegram/webhook', methods=['POST'])
def telegram_webhook_route():
    """POST /api/telegram/webhook - Recibe updates de Telegram vía webhook"""
    return telegram_webhook_controller.handle_webhook()


@api.route('/telegram/webhook/set', methods=['POST'])
@require_auth
def set_telegram_webhook_route():
    """POST /api/telegram/webhook/set - Configura webhook en Telegram (admin only)"""
    data = request.get_json()
    webhook_url = data.get('webhook_url')

    if not webhook_url:
        return {'error': 'webhook_url requerido'}, 400

    return telegram_webhook_controller.set_webhook(webhook_url)


@api.route('/telegram/webhook/delete', methods=['POST'])
@require_auth
def delete_telegram_webhook_route():
    """POST /api/telegram/webhook/delete - Elimina webhook de Telegram (admin only)"""
    return telegram_webhook_controller.delete_webhook()


@api.route('/telegram/webhook/info', methods=['GET'])
@require_auth
def get_telegram_webhook_info_route():
    """GET /api/telegram/webhook/info - Obtiene info del webhook actual"""
    return telegram_webhook_controller.get_webhook_info()


# ============================================================================
# INTERNAL: SOCKET EMIT (for external processes like Telegram bot)
# ============================================================================

@api.route('/internal/socket/emit', methods=['POST'])
def internal_socket_emit():
    """POST /api/internal/socket/emit - Emite eventos WebSocket desde procesos externos"""
    from flask import request
    from app.services.socket_service import emit_sync_update, emit_status_update

    data = request.get_json()
    room = data.get('room')
    event = data.get('event')
    event_data = data.get('data', {})

    if not room or not event:
        return {'error': 'room y event son requeridos'}, 400

    # Extraer sync_code del room (formato: sync_XXXXXX)
    if room.startswith('sync_'):
        sync_code = room.replace('sync_', '')

        # Si es refresh_status, llamar a emit_status_update
        if event == 'refresh_status':
            emit_status_update(sync_code)
        else:
            # Emitir el evento directamente
            emit_sync_update(sync_code, event, event_data)

        return {'status': 'ok', 'message': f'Evento {event} emitido a {room}'}, 200

    return {'error': 'Formato de room inválido'}, 400


# ============================================================================
# HEALTH CHECK
# ============================================================================

@api.route('/health', methods=['GET'])
def health_check():
    """GET /api/health - Health check endpoint"""
    return {'status': 'ok', 'message': 'API funcionando correctamente'}, 200
