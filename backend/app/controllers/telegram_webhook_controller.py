"""
Telegram Webhook Controller - Controlador para recibir updates de Telegram vía webhook
"""
import os
import json
from flask import request, jsonify
from telegram import Update
from telegram.ext import ContextTypes
from app.services.telegram_bot import setup_bot_application
import asyncio
from functools import wraps

# Configuración
WEBHOOK_SECRET = os.getenv('TELEGRAM_WEBHOOK_SECRET', '')

# Aplicación del bot (singleton)
_bot_application = None
_bot_initialized = False


def get_bot_application_sync():
    """Obtiene la aplicación del bot (versión síncrona, sin inicializar)"""
    global _bot_application

    if _bot_application is None:
        _bot_application = setup_bot_application()

    return _bot_application


async def get_bot_application():
    """Obtiene la aplicación del bot (singleton) y la inicializa si es necesario"""
    global _bot_application, _bot_initialized

    if _bot_application is None:
        _bot_application = setup_bot_application()

    # Inicializar solo la primera vez
    if not _bot_initialized:
        await _bot_application.initialize()
        _bot_initialized = True
        print("✅ Bot application inicializada para webhooks")

    return _bot_application


def async_handler(f):
    """Decorator para ejecutar funciones async en contexto sync de Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Intentar obtener el loop actual, o crear uno nuevo
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # NO cerrar el loop después de ejecutar, para permitir que las respuestas asíncronas se completen
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapper


@async_handler
async def handle_webhook():
    """
    POST /api/telegram/webhook
    Endpoint para recibir updates de Telegram vía webhook
    """
    try:
        # Verificar que sea POST
        if request.method != 'POST':
            return jsonify({'error': 'Method not allowed'}), 405

        # Verificar secret token (opcional pero recomendado)
        if WEBHOOK_SECRET:
            secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
            if secret_header != WEBHOOK_SECRET:
                print("⚠️  Webhook rechazado: secret token inválido")
                return jsonify({'error': 'Unauthorized'}), 401

        # Obtener el update de Telegram
        update_data = request.get_json(force=True)

        if not update_data:
            return jsonify({'error': 'Invalid update data'}), 400

        # Obtener aplicación del bot (inicializa si es necesario)
        application = await get_bot_application()

        if not application:
            return jsonify({'error': 'Bot not initialized'}), 500

        # Convertir JSON a objeto Update de python-telegram-bot
        update = Update.de_json(update_data, application.bot)

        # Procesar el update de forma asíncrona
        await application.process_update(update)

        # Telegram espera 200 OK
        return jsonify({'ok': True}), 200

    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        import traceback
        traceback.print_exc()
        # Telegram reintentará si devolvemos error
        return jsonify({'error': str(e)}), 500


def set_webhook(webhook_url: str):
    """
    Configura el webhook en Telegram

    Args:
        webhook_url: URL completa del webhook (ej: https://tu-dominio.com/api/telegram/webhook)

    Returns:
        dict con resultado de la operación
    """
    try:
        application = get_bot_application_sync()

        if not application:
            return {'success': False, 'error': 'Bot not initialized'}

        # Configurar webhook con python-telegram-bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Parámetros del webhook
            webhook_params = {
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query', 'edited_message'],
                'drop_pending_updates': True  # Ignorar updates pendientes al configurar
            }

            # Agregar secret token si está configurado
            if WEBHOOK_SECRET:
                webhook_params['secret_token'] = WEBHOOK_SECRET

            # Configurar webhook
            result = loop.run_until_complete(
                application.bot.set_webhook(**webhook_params)
            )

            if result:
                print(f"✅ Webhook configurado exitosamente: {webhook_url}")
                return {
                    'success': True,
                    'webhook_url': webhook_url,
                    'message': 'Webhook configurado correctamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'Telegram rechazó la configuración del webhook'
                }

        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def delete_webhook():
    """
    Elimina el webhook de Telegram (útil para volver a polling en desarrollo)

    Returns:
        dict con resultado de la operación
    """
    try:
        application = get_bot_application_sync()

        if not application:
            return {'success': False, 'error': 'Bot not initialized'}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                application.bot.delete_webhook(drop_pending_updates=True)
            )

            if result:
                print("✅ Webhook eliminado exitosamente")
                return {'success': True, 'message': 'Webhook eliminado'}
            else:
                return {'success': False, 'error': 'No se pudo eliminar el webhook'}

        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Error eliminando webhook: {e}")
        return {'success': False, 'error': str(e)}


def get_webhook_info():
    """
    Obtiene información del webhook actual

    Returns:
        dict con información del webhook
    """
    try:
        application = get_bot_application_sync()

        if not application:
            return {'success': False, 'error': 'Bot not initialized'}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            webhook_info = loop.run_until_complete(
                application.bot.get_webhook_info()
            )

            return {
                'success': True,
                'webhook_info': {
                    'url': webhook_info.url,
                    'has_custom_certificate': webhook_info.has_custom_certificate,
                    'pending_update_count': webhook_info.pending_update_count,
                    'last_error_date': webhook_info.last_error_date,
                    'last_error_message': webhook_info.last_error_message,
                    'max_connections': webhook_info.max_connections,
                    'allowed_updates': webhook_info.allowed_updates
                }
            }

        finally:
            loop.close()

    except Exception as e:
        print(f"❌ Error obteniendo info del webhook: {e}")
        return {'success': False, 'error': str(e)}
