"""
Telegram Bot - Bot de control para presentaciones
"""
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# Configuración
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')

# Helper para persistencia en BD
from app.services.telegram_session_helper import (
    get_sync_code, get_pending_data, set_pending_data, delete_pending_data
)

# Database access para control_message_id
from app.database import get_db
from app.models.sync_session import SyncSession

# Estado del usuario
control_messages = {}  # chat_id -> message_id del control (no crítico, puede estar en memoria)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Muestra la ayuda con todos los comandos disponibles"""
    await update.message.reply_text(
        "📚 Comandos disponibles:\n\n"
        "/start - Iniciar el bot\n"
        "/sync CODIGO - Sincronizar con presentación\n"
        "/status - Ver estado de conexión\n"
        "/ejemplo TEMA - Generar ejemplo con IA\n"
        "/pregunta - Generar pregunta con IA\n"
        "/analogia - Generar analogías simples\n"
        "/disconnect - Desconectar control\n"
        "/help - Mostrar esta ayuda\n\n"
        "💡 Tip: Puedes enviar un audio de voz para generar ejemplos"
    )
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Inicia el bot"""
    await update.message.reply_text(
        "👋 ¡Bienvenido al Sistema de Control de Presentaciones!\n\n"
        "Para conectar tu control:\n"
        "1. Inicia una clase en la plataforma web\n"
        "2. Usa el comando /sync CÓDIGO\n\n"
        "Comandos disponibles:\n"
        "/sync CODIGO - Sincronizar con presentación\n"
        "/status - Ver estado de conexión\n"
        "/ejemplo TEMA - Generar ejemplo con IA (texto o audio)\n"
        "/pregunta - Generar pregunta con IA (solo texto)\n"
        "/analogia - Generar analogías simples para explicar\n"
        "/disconnect - Desconectar control\n"
        "/help - Mostrar esta ayuda\n\n"
        "💡 Tip: Puedes enviar un audio de voz para generar ejemplos"
    )


async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /sync CODIGO - Sincroniza con una presentación"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Verificar que se proporcionó el código
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Debes proporcionar el código de sincronización.\n"
            "Uso: /sync ABC123\n\n"
            "Usa /help para ver todos los comandos disponibles." 
        )
        return

    sync_code = context.args[0].upper()

    # Llamar al API para sincronizar
    try:
        response = requests.post(
            f"{API_BASE_URL}/sync/pair",
            json={
                'sync_code': sync_code,
                'telegram_chat_id': str(chat_id),
                'telegram_user_id': str(user_id)
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Verificar si la instancia está activa desde la respuesta de pair
            is_instance_active = data.get('is_instance_active', True)

            if not is_instance_active:
                await update.message.reply_text(
                    f"🔴 La clase ya ha finalizado\n\n"
                    f"Esta presentación ya no está activa."
                )
                return

            # Sesión ya guardada en BD por el endpoint /sync/pair
            await update.message.reply_text(
                f"✅ ¡Sincronización exitosa!\n\n"
                f"Código: {sync_code}\n"
                f"Usa los botones para controlar la presentación."
            )

            # Enviar o actualizar teclado de control
            # send_control_keyboard ya maneja eliminar duplicados automáticamente
            await send_control_keyboard(update, chat_id)

        else:
            error_msg = response.json().get('error', 'Error desconocido')
            await update.message.reply_text(
                f"❌ Error al sincronizar: {error_msg}\n\n"
                f"Verifica que el código sea correcto.\n"
                f"Usa /help para ver todos los comandos disponibles."
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error de conexión: {str(e)}\n"
            f"Verifica que el servidor esté funcionando.\n"
            f"Usa /help para ver todos los comandos disponibles."
        )


def get_control_keyboard():
    """Retorna el teclado de control inline"""
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Anterior", callback_data="prev"),
            InlineKeyboardButton("▶️ Siguiente", callback_data="next")
        ],
        [
            InlineKeyboardButton("⏸️ Pausar", callback_data="pause"),
            InlineKeyboardButton("▶️ Reanudar", callback_data="resume")
        ],
        [
            InlineKeyboardButton("📊 Estado", callback_data="status")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_control_keyboard(update: Update, chat_id: int):
    """
    Envía o actualiza el teclado de control

    Elimina cualquier control anterior antes de enviar uno nuevo (usando BD para persistencia)
    """
    reply_markup = get_control_keyboard()
    bot = update.get_bot()

    # Obtener sync_code para consultar la BD
    sync_code = get_sync_code(chat_id)

    if sync_code:
        # Consultar la BD para obtener el control_message_id anterior
        db = next(get_db())
        try:
            sync_session = db.query(SyncSession).filter(
                SyncSession.sync_code == sync_code,
                SyncSession.is_active == True
            ).first()

            if sync_session and sync_session.control_message_id:
                old_message_id = sync_session.control_message_id
                try:
                    await bot.delete_message(
                        chat_id=chat_id,
                        message_id=int(old_message_id)
                    )
                    print(f"[DEBUG] Control anterior eliminado desde BD (message_id: {old_message_id})")
                except Exception as e:
                    # Mensaje ya fue eliminado manualmente o no existe
                    print(f"[DEBUG] No se pudo eliminar mensaje anterior (posiblemente ya eliminado): {e}")

                # Limpiar el control_message_id de la BD
                sync_session.control_message_id = None
                db.commit()

        except Exception as e:
            print(f"[ERROR] Error al buscar control anterior en BD: {e}")
        finally:
            db.close()

    # Verificar que tenemos un mensaje de update
    if not update.message:
        print(f"[ERROR] No se puede enviar control: update.message es None")
        return

    # Enviar nuevo control
    try:
        message = await update.message.reply_text(
            "🎮 Control de Presentación:",
            reply_markup=reply_markup
        )

        # Guardar el message_id en memoria (para acceso rápido, pero no crítico)
        control_messages[chat_id] = message.message_id

        # Guardar el message_id en la BD (para persistencia entre workers/reinicios)
        if sync_code:
            db = next(get_db())
            try:
                sync_session = db.query(SyncSession).filter(
                    SyncSession.sync_code == sync_code,
                    SyncSession.is_active == True
                ).first()

                if sync_session:
                    sync_session.control_message_id = str(message.message_id)
                    db.commit()
                    print(f"[DEBUG] Nuevo control enviado y guardado en BD (message_id: {message.message_id})")
                else:
                    print(f"[WARNING] No se pudo guardar control_message_id: sesión no encontrada")

            except Exception as e:
                print(f"[ERROR] Error al guardar control_message_id en BD: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print(f"[DEBUG] Nuevo control enviado (message_id: {message.message_id})")

    except Exception as e:
        print(f"[ERROR] No se pudo enviar control: {e}")
        import traceback
        traceback.print_exc()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los botones del control"""
    query = update.callback_query

    # Intentar responder al callback (puede fallar si expiró)
    try:
        await query.answer()
    except Exception as e:
        print(f"[DEBUG] Could not answer callback query: {e}")
        # Continuar de todas formas

    chat_id = update.effective_chat.id
    command = query.data

    # Manejar callbacks de ejemplos
    if command.startswith('example_'):
        await handle_example_callback(query, chat_id, command)
        return

    # Manejar callbacks de preguntas
    if command.startswith('question_'):
        await handle_question_callback(query, chat_id, command)
        return

    # Manejar callbacks de analogías
    if command.startswith('analogy_'):
        await handle_analogy_callback(query, chat_id, command)
        return

    # Verificar si está sincronizado
    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await query.edit_message_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    

    # Comando de estado
    if command == "status":
        try:
            response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")
            if response.status_code == 200:
                data = response.json()
                sync_session = data.get('sync_session', {})
                slide = sync_session.get('current_slide', 1)
                is_connected = data.get('is_connected', False)
                is_instance_active = data.get('is_instance_active', False)

                status_text = (
                    f"📊 Estado de la Presentación:\n\n"
                    f"Código: {sync_code}\n"
                    f"Conectado: {'✅ Sí' if is_connected else '❌ No'}\n"
                    f"Estado: {'▶️ En curso' if is_instance_active else '🔴 Finalizada'}\n"
                    f"Diapositiva actual: {slide}"
                )

                try:
                    await query.edit_message_text(
                        status_text,
                        reply_markup=get_control_keyboard()
                    )
                except Exception as edit_error:
                    # Si el mensaje no cambió, ignorar el error
                    if "message is not modified" not in str(edit_error).lower():
                        raise
            else:
                await query.edit_message_text("❌ Error al obtener estado")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
        return

    # Enviar comando
    try:
        response = requests.post(
            f"{API_BASE_URL}/sync/{sync_code}/command",
            json={'command': command}
        )

        if response.status_code == 400:
            # La clase ya finalizó
            error_data = response.json()
            error_message = error_data.get('error', 'Error desconocido')

            await query.edit_message_text(
                f"🔴 {error_message}\n\n"
                f"Esta presentación ya no está activa.\n"
                f"Usa /disconnect para desconectar el control."
            )
            return

        if response.status_code == 200:
            data = response.json()
            sync_session = data.get('sync_session', {})
            slide = sync_session.get('current_slide', 1)

            emoji_map = {
                'next': '▶️',
                'prev': '⬅️',
                'pause': '⏸️',
                'resume': '▶️'
            }

            new_text = (
                f"{emoji_map.get(command, '✅')} Comando enviado: {command}\n"
                f"Diapositiva actual: {slide}"
            )

            try:
                await query.edit_message_text(
                    new_text,
                    reply_markup=get_control_keyboard()
                )
            except Exception as edit_error:
                # Si falla por mensaje idéntico, ignorar el error
                if "message is not modified" not in str(edit_error).lower():
                    raise

        else:
            await query.edit_message_text(
                f"❌ Error al enviar comando"
            )

    except Exception as e:
        # Solo mostrar el error si no es por mensaje idéntico
        if "message is not modified" not in str(e).lower():
            await query.edit_message_text(
                f"❌ Error de conexión: {str(e)}"
            )


async def disconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /disconnect - Desconecta el control

    Elimina el control del chat de Telegram y desconecta del backend
    """
    chat_id = update.effective_chat.id

    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await update.message.reply_text("❌ No estás sincronizado.")
        return

    try:
        # Llamar al API para desconectar
        response = requests.post(f"{API_BASE_URL}/sync/{sync_code}/disconnect")

        if response.status_code == 200:
            # Eliminar mensaje de control desde la BD
            db = next(get_db())
            try:
                sync_session = db.query(SyncSession).filter(
                    SyncSession.sync_code == sync_code,
                    SyncSession.is_active == True
                ).first()

                if sync_session and sync_session.control_message_id:
                    old_message_id = sync_session.control_message_id
                    try:
                        await update.get_bot().delete_message(
                            chat_id=chat_id,
                            message_id=int(old_message_id)
                        )
                        print(f"[DEBUG] Control eliminado al desconectar desde BD (message_id: {old_message_id})")
                    except Exception as e:
                        # El mensaje puede haber sido eliminado manualmente
                        print(f"[DEBUG] No se pudo eliminar mensaje de control (posiblemente ya eliminado): {e}")

                    # Limpiar el control_message_id de la BD
                    sync_session.control_message_id = None
                    db.commit()

            except Exception as e:
                print(f"[ERROR] Error al eliminar control desde BD: {e}")
            finally:
                db.close()

            # También limpiar de memoria si existe
            if chat_id in control_messages:
                del control_messages[chat_id]

            await update.message.reply_text(
                "✅ Control desconectado exitosamente.\n\n"
                "Usa /sync CODIGO para conectar nuevamente cuando lo necesites."
            )
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_msg = error_data.get('error', 'Error desconocido')
            await update.message.reply_text(f"❌ Error al desconectar: {error_msg}")

    except Exception as e:
        print(f"[ERROR] Error en disconnect_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ Error de conexión: {str(e)}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Muestra el estado actual"""
    chat_id = update.effective_chat.id

    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await update.message.reply_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    try:
        response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")

        if response.status_code == 200:
            data = response.json()
            sync_session = data.get('sync_session', {})
            slide = sync_session.get('current_slide', 1)
            is_connected = data.get('is_connected', False)
            is_instance_active = data.get('is_instance_active', False)
            last_command = sync_session.get('last_command', 'Ninguno')

            await update.message.reply_text(
                f"📊 Estado de la Presentación:\n\n"
                f"Código: {sync_code}\n"
                f"Conectado: {'✅ Sí' if is_connected else '❌ No'}\n"
                f"Estado: {'▶️ En curso' if is_instance_active else '🔴 Finalizada'}\n"
                f"Diapositiva actual: {slide}\n"
                f"Último comando: {last_command}"
            )
        else:
            await update.message.reply_text("❌ Error al obtener estado")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_example_callback(query, chat_id: int, callback_data: str):
    """Maneja las interacciones con los botones de ejemplos"""
    req_data = get_pending_data(chat_id, 'example_request')
    if not req_data:
        await query.edit_message_text("❌ Solicitud expirada. Usa /ejemplo nuevamente.")
        return
    
    request_id = req_data['request_id']

    # Seleccionar una opción
    if callback_data.startswith('example_select_'):
        option_index = int(callback_data.split('_')[2])

        try:
            # Informar que se está procesando
            await query.edit_message_text("⏳ Generando diapositiva con el ejemplo seleccionado...")

            # Enviar selección al backend
            response = requests.post(
                f"{API_BASE_URL}/example/{request_id}/select",
                json={'option_index': option_index}
            )

            if response.status_code == 200:
                data = response.json()
                new_slide_index = data.get('new_slide_index')
                total_slides = data.get('total_slides')

                # Eliminar solicitud pendiente
                delete_pending_data(chat_id, 'example_request')

                await query.edit_message_text(
                    f"✅ ¡Ejemplo generado exitosamente!\n\n"
                    f"📊 Nueva diapositiva creada en posición {new_slide_index}\n"
                    f"Total de diapositivas: {total_slides}\n\n"
                    f"La diapositiva ha sido marcada como generada por IA."
                )
            else:
                error_data = response.json()
                await query.edit_message_text(
                    f"❌ Error al generar diapositiva:\n{error_data.get('error', 'Error desconocido')}"
                )

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    # Regenerar opciones
    elif callback_data == 'example_regenerate':
        try:
            await query.edit_message_text("⏳ Generando nuevas opciones...")

            response = requests.post(f"{API_BASE_URL}/example/{request_id}/regenerate")

            if response.status_code == 200:
                data = response.json()
                new_options = data.get('options', [])
                topic = req_data['topic']

                # Actualizar solicitud
                set_pending_data(chat_id, 'example_request', req_data)

                # Crear teclado con nuevas opciones
                keyboard = []
                for i, option in enumerate(new_options):
                    keyboard.append([InlineKeyboardButton(f"Opción {i+1}", callback_data=f"example_select_{i}")])

                keyboard.append([InlineKeyboardButton("🔄 Más opciones", callback_data="example_regenerate")])
                keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="example_cancel")])

                reply_markup = InlineKeyboardMarkup(keyboard)

                # Mostrar nuevas opciones
                options_text = f"🤖 Nuevas opciones generadas sobre: {topic}\n\n"
                for i, option in enumerate(new_options):
                    options_text += f"📝 Opción {i+1}:\n{option[:200]}{'...' if len(option) > 200 else ''}\n\n"

                await query.edit_message_text(
                    options_text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("❌ Error al regenerar opciones")

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    # Cancelar solicitud
    elif callback_data == 'example_cancel':
        try:
            requests.post(f"{API_BASE_URL}/example/{request_id}/cancel")
            delete_pending_data(chat_id, 'example_request')
            await query.edit_message_text("❌ Solicitud de ejemplo cancelada.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")


async def handle_analogy_callback(query, chat_id: int, callback_data: str):
    """Maneja las interacciones con los botones de analogías"""
    req_data = get_pending_data(chat_id, 'analogy_request')
    if not req_data:
        await query.edit_message_text("❌ Solicitud expirada. Usa /analogia nuevamente.")
        return

    request_id = req_data['request_id']
    analogies = req_data['analogies']
    sync_code = req_data['sync_code']

    # Seleccionar una analogía
    if callback_data.startswith('analogy_') and callback_data != 'analogy_cancel':
        try:
            option_index = int(callback_data.split('_')[1])

            if option_index >= len(analogies):
                await query.edit_message_text("❌ Opción inválida")
                return

            # Informar que se está procesando
            await query.edit_message_text("⏳ Generando diapositiva con la analogía seleccionada...")

            # Enviar selección al backend
            response = requests.post(
                f"{API_BASE_URL}/ai/analogy/select",
                json={
                    'request_id': request_id,
                    'option_index': option_index,
                    'sync_code': sync_code
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                new_slide_index = data.get('new_slide_index')
                total_slides = data.get('total_slides')

                # Eliminar solicitud pendiente
                delete_pending_data(chat_id, 'analogy_request')

                await query.edit_message_text(
                    f"✅ ¡Analogía generada exitosamente!\n\n"
                    f"💡 Nueva diapositiva de ejemplo creada en posición {new_slide_index}\n"
                    f"Total de diapositivas: {total_slides}\n\n"
                    f"La diapositiva ha sido marcada como 'Ejemplo con analogía (IA)'."
                )
            else:
                error_data = response.json()
                await query.edit_message_text(
                    f"❌ Error al generar diapositiva:\n{error_data.get('error', 'Error desconocido')}"
                )

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    # Cancelar
    elif callback_data == 'analogy_cancel':
        try:
            delete_pending_data(chat_id, 'analogy_request')
            await query.edit_message_text("❌ Solicitud de analogía cancelada.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")


async def example_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ejemplo TEMA - Solicita generar ejemplos con IA"""
    chat_id = update.effective_chat.id
    sync_code = get_sync_code(chat_id)

    if not sync_code:
        await update.message.reply_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar primero.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    # Verificar que la instancia esté activa
    status_response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")

    if status_response.status_code == 200:
        status_data = status_response.json()
        if not status_data.get('is_instance_active', False):
            await update.message.reply_text(
                "❌ La clase ya finalizó.\n\n"
                "No se pueden generar más ejemplos después de finalizar la clase."
            )
            return
    else:
        await update.message.reply_text("❌ Error al verificar estado de la sesión")
        return

    # Verificar que se proporcionó el tema
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Uso incorrecto.\n\n"
            "Formato: /ejemplo TEMA\n"
            "Ejemplo: /ejemplo ecuaciones cuadráticas"
        )
        return

    topic = ' '.join(context.args)

    try:
        # Solicitar generación de ejemplos al backend
        response = requests.post(
            f"{API_BASE_URL}/sync/{sync_code}/example/request",
            json={'topic': topic}
        )

        if response.status_code == 200:
            data = response.json()
            request_id = data.get('request_id')
            options = data.get('options', [])

            # Guardar solicitud pendiente
            set_pending_data(chat_id, 'example_request', {
                'request_id': request_id,
                'options': options,
                'topic': topic
            })

            # Crear teclado con opciones
            keyboard = []
            for i, option in enumerate(options):
                # Truncar texto para el botón
                button_text = option[:50] + "..." if len(option) > 50 else option
                keyboard.append([InlineKeyboardButton(f"Opción {i+1}", callback_data=f"example_select_{i}")])

            keyboard.append([InlineKeyboardButton("🔄 Más opciones", callback_data="example_regenerate")])
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="example_cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Mostrar opciones
            options_text = f"🤖 Ejemplos generados sobre: {topic}\n\n"
            for i, option in enumerate(options):
                options_text += f"📝 Opción {i+1}:\n{option[:200]}{'...' if len(option) > 200 else ''}\n\n"

            await update.message.reply_text(
                options_text,
                reply_markup=reply_markup
            )

        elif response.status_code == 400:
            error_data = response.json()
            await update.message.reply_text(f"❌ {error_data.get('error', 'Error desconocido')}")
        else:
            await update.message.reply_text("❌ Error al generar ejemplos")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_question_callback(query, chat_id: int, callback_data: str):
    """Maneja las interacciones con los botones de preguntas"""
    req_data = get_pending_data(chat_id, 'question_request')
    if not req_data:
        await query.edit_message_text("❌ Solicitud expirada. Usa /pregunta nuevamente.")
        return
    request_id = req_data['request_id']
    question_type = req_data['question_type']

    # Seleccionar tipo de pregunta
    if callback_data in ['question_type_multiple', 'question_type_open']:
        selected_type = 'multiple-choice' if 'multiple' in callback_data else 'open'

        try:
            await query.edit_message_text("⏳ Generando preguntas basadas en el contenido...")

            # Obtener sync_code de la sesión
            sync_code = get_sync_code(chat_id)
            if not sync_code:
                await query.edit_message_text("❌ No estás sincronizado. Usa /sync primero.")
                return

            # Obtener custom_prompt si existe
            custom_prompt = req_data.get('custom_prompt', '')

            # Solicitar generación de preguntas al backend
            response = requests.post(
                f"{API_BASE_URL}/sync/{sync_code}/question/request",
                json={
                    'question_type': selected_type,
                    'custom_prompt': custom_prompt
                }
            )

            if response.status_code == 200:
                data = response.json()
                new_request_id = data.get('request_id')
                options = data.get('options', [])

                # Actualizar solicitud pendiente
                req_data['request_id'] = new_request_id
                req_data['options'] = options
                req_data['question_type'] = selected_type
                
                set_pending_data(chat_id, 'question_request', req_data)

                # Crear teclado con opciones
                keyboard = []
                for i, option in enumerate(options):
                    keyboard.append([InlineKeyboardButton(f"Opción {i+1}", callback_data=f"question_select_{i}")])

                keyboard.append([InlineKeyboardButton("🔄 Más opciones", callback_data="question_regenerate")])
                keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="question_cancel")])

                reply_markup = InlineKeyboardMarkup(keyboard)

                # Mostrar opciones
                type_label = "con alternativas" if selected_type == "multiple-choice" else "abierta"
                options_text = f"🤖 Preguntas generadas (tipo: {type_label}):\n\n"
                for i, option in enumerate(options):
                    options_text += f"📝 Opción {i+1}:\n{option[:300]}{'...' if len(option) > 300 else ''}\n\n"

                await query.edit_message_text(
                    options_text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("❌ Error al generar preguntas")

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
        return

    # Seleccionar una opción de pregunta
    if callback_data.startswith('question_select_'):
        option_index = int(callback_data.split('_')[2])

        try:
            await query.edit_message_text("⏳ Generando diapositiva con la pregunta seleccionada...")

            # Enviar selección al backend
            response = requests.post(
                f"{API_BASE_URL}/question/{request_id}/select",
                json={'option_index': option_index}
            )

            if response.status_code == 200:
                data = response.json()
                new_slide_index = data.get('new_slide_index')
                total_slides = data.get('total_slides')

                # Eliminar solicitud pendiente
                delete_pending_data(chat_id, 'question_request')

                await query.edit_message_text(
                    f"✅ ¡Pregunta generada exitosamente!\n\n"
                    f"📊 Nueva diapositiva creada en posición {new_slide_index}\n"
                    f"Total de diapositivas: {total_slides}\n\n"
                    f"La diapositiva ha sido marcada como generada por IA.\n"
                    "Usa /help para ver todos los comandos disponibles."
                )
            else:
                error_data = response.json()
                await query.edit_message_text(
                    f"❌ Error al generar diapositiva:\n{error_data.get('error', 'Error desconocido')}"
                )

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    # Regenerar opciones
    elif callback_data == 'question_regenerate':
        try:
            await query.edit_message_text("⏳ Generando nuevas opciones...")

            response = requests.post(f"{API_BASE_URL}/question/{request_id}/regenerate")

            if response.status_code == 200:
                data = response.json()
                new_options = data.get('options', [])
                question_type = req_data['question_type']

                # Actualizar solicitud
                req_data['options'] = new_options
                set_pending_data(chat_id, 'question_request', req_data)

                # Crear teclado con nuevas opciones
                keyboard = []
                for i, option in enumerate(new_options):
                    keyboard.append([InlineKeyboardButton(f"Opción {i+1}", callback_data=f"question_select_{i}")])

                keyboard.append([InlineKeyboardButton("🔄 Más opciones", callback_data="question_regenerate")])
                keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="question_cancel")])

                reply_markup = InlineKeyboardMarkup(keyboard)

                # Mostrar nuevas opciones
                type_label = "con alternativas" if question_type == "multiple-choice" else "abierta"
                options_text = f"🤖 Nuevas preguntas generadas (tipo: {type_label}):\n\n"
                for i, option in enumerate(new_options):
                    options_text += f"📝 Opción {i+1}:\n{option[:300]}{'...' if len(option) > 300 else ''}\n\n"

                await query.edit_message_text(
                    options_text,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("❌ Error al regenerar opciones")

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    # Cancelar solicitud
    elif callback_data == 'question_cancel':
        try:
            requests.post(f"{API_BASE_URL}/question/{request_id}/cancel")
            delete_pending_data(chat_id, 'question_request')
            await query.edit_message_text("❌ Solicitud de pregunta cancelada.")
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")


async def question_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pregunta - Solicita generar preguntas con IA (solo texto)"""
    chat_id = update.effective_chat.id

    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await update.message.reply_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar primero.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    # Verificar que la instancia esté activa
    status_response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")

    if status_response.status_code == 200:
        status_data = status_response.json()
        if not status_data.get('is_instance_active', False):
            await update.message.reply_text(
                "❌ La clase ya finalizó.\n\n"
                "No se pueden generar más preguntas después de finalizar la clase."
            )
            return
    else:
        await update.message.reply_text("❌ Error al verificar estado de la sesión")
        return

    # Capturar tema/prompt opcional del usuario (ej: /pregunta el rol de la mujer)
    custom_prompt = ' '.join(context.args) if context.args else ""

    # Crear teclado para elegir tipo de pregunta
    keyboard = [
        [InlineKeyboardButton("📝 Con alternativas (A, B, C, D)", callback_data="question_type_multiple")],
        [InlineKeyboardButton("✍️ Abierta (desarrollo)", callback_data="question_type_open")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Guardar solicitud inicial (sin request_id aún, pero con custom_prompt)
    set_pending_data(chat_id, 'question_request', {
        'request_id': None,
        'options': [],
        'question_type': None,
        'custom_prompt': custom_prompt
    })

    prompt_text = f"\n\nTema: {custom_prompt}" if custom_prompt else ""

    await update.message.reply_text(
        f"🤖 Generación de Pregunta con IA{prompt_text}\n\n"
        "Selecciona el tipo de pregunta que deseas generar:\n\n"
        "📝 Con alternativas: pregunta de opción múltiple (4 alternativas)\n"
        "✍️ Abierta: pregunta de desarrollo\n\n"
        "La pregunta se generará basada en el contenido de las diapositivas hasta la actual.",
        reply_markup=reply_markup
    )


async def analogy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /analogia - Genera analogías simples para explicar conceptos"""
    chat_id = update.effective_chat.id

    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await update.message.reply_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar primero.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    # Verificar que la instancia esté activa
    status_response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")

    if status_response.status_code == 200:
        status_data = status_response.json()
        if not status_data.get('is_instance_active', False):
            await update.message.reply_text(
                "❌ La clase ya finalizó.\n\n"
                "No se pueden generar más analogías después de finalizar la clase."
            )
            return
    else:
        await update.message.reply_text("❌ Error al verificar estado de la sesión")
        return

    # Notificar que se está generando
    processing_msg = await update.message.reply_text(
        "🤖 Analizando la diapositiva actual...\n"
        "Generando 2-3 analogías simples para explicar el concepto.\n\n"
        "Esto puede tardar unos segundos."
    )

    try:
        # Solicitar generación de analogías
        response = requests.post(
            f"{API_BASE_URL}/ai/analogy/generate",
            json={'sync_code': sync_code},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            request_id = data.get('request_id')
            analogies = data.get('analogies', [])

            if not analogies or len(analogies) == 0:
                await processing_msg.edit_text("❌ No se pudieron generar analogías para esta diapositiva.")
                return

            # Guardar datos pendientes
            set_pending_data(chat_id, 'analogy_request', {
                'request_id': request_id,
                'analogies': analogies,
                'sync_code': sync_code
            })

            # Eliminar mensaje de "generando..."
            await processing_msg.delete()

            # Crear teclado con las opciones de analogías
            keyboard = []
            for i, analogy in enumerate(analogies[:3]):  # Máximo 3
                # Truncar para el botón
                button_text = analogy[:60] + "..." if len(analogy) > 60 else analogy
                keyboard.append([InlineKeyboardButton(
                    f"{i+1}. {button_text}",
                    callback_data=f"analogy_{i}"
                )])

            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="analogy_cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Mostrar opciones completas
            analogies_text = "\n\n".join([f"{i+1}. {a}" for i, a in enumerate(analogies[:3])])

            await update.message.reply_text(
                f"💡 *Analogías Generadas*\n\n"
                f"{analogies_text}\n\n"
                f"Selecciona una para crear una diapositiva de ejemplo:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif response.status_code == 400:
            error_msg = response.json().get('error', 'Error desconocido')
            await processing_msg.edit_text(f"❌ {error_msg}")
        else:
            await processing_msg.edit_text("❌ Error al generar analogías")

    except requests.exceptions.Timeout:
        await processing_msg.edit_text(
            "❌ La generación está tomando mucho tiempo.\n"
            "Intenta nuevamente."
        )
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de voz para generar ejemplos"""
    chat_id = update.effective_chat.id

    sync_code = get_sync_code(chat_id)
    if not sync_code:
        await update.message.reply_text(
            "❌ No estás sincronizado.\n"
            "Usa /sync CODIGO para conectar primero.\n"
            "Usa /help para ver todos los comandos disponibles."
        )
        return

    # Verificar que la instancia esté activa
    status_response = requests.get(f"{API_BASE_URL}/sync/{sync_code}/status")

    if status_response.status_code == 200:
        status_data = status_response.json()
        if not status_data.get('is_instance_active', False):
            await update.message.reply_text(
                "❌ La clase ya finalizó.\n\n"
                "No se pueden generar más ejemplos después de finalizar la clase."
            )
            return
    else:
        await update.message.reply_text("❌ Error al verificar estado de la sesión")
        return

    try:
        # Obtener el archivo de voz
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        # Descargar el archivo de audio
        audio_path = f"/tmp/voice_{chat_id}_{voice.file_id}.ogg"
        await voice_file.download_to_drive(audio_path)

        await update.message.reply_text("🎤 Audio recibido. Transcribiendo...")

        # Importar librería para transcripción
        try:
            import google.generativeai as genai
            import os

            GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
            genai.configure(api_key=GEMINI_API_KEY)

            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            # Leer archivo de audio
            with open(audio_path, 'rb') as audio_file:
                audio_file_obj = genai.upload_file(audio_path)

            # Transcribir con Gemini
            response = model.generate_content([
                "Transcribe este audio a texto. Responde SOLO con la transcripción, sin agregar nada más.",
                audio_file_obj
            ])

            transcript = response.text.strip()

            # Eliminar archivo temporal
            os.remove(audio_path)

            await update.message.reply_text(f"📝 Transcripción: {transcript}\n\n⏳ Generando ejemplos...")

            # Usar el texto transcrito como tema para generar ejemplos
            # Obtener sync_code de la sesión
            sync_code = get_sync_code(chat_id)
            if not sync_code:
                await update.message.reply_text("❌ No estás sincronizado. Usa /sync primero.")
                return

            response = requests.post(
                f"{API_BASE_URL}/sync/{sync_code}/example/request",
                json={'topic': transcript}
            )

            if response.status_code == 200:
                data = response.json()
                request_id = data.get('request_id')
                options = data.get('options', [])

                # Guardar solicitud pendiente en base de datos
                set_pending_data(chat_id, 'example_request', {
                    'request_id': request_id,
                    'options': options,
                    'topic': transcript
                })

                # Crear teclado con opciones
                keyboard = []
                for i, option in enumerate(options):
                    keyboard.append([InlineKeyboardButton(f"Opción {i+1}", callback_data=f"example_select_{i}")])

                keyboard.append([InlineKeyboardButton("🔄 Más opciones", callback_data="example_regenerate")])
                keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="example_cancel")])

                reply_markup = InlineKeyboardMarkup(keyboard)

                # Mostrar opciones
                options_text = f"🤖 Ejemplos generados sobre: {transcript}\n\n"
                for i, option in enumerate(options):
                    options_text += f"📝 Opción {i+1}:\n{option[:200]}{'...' if len(option) > 200 else ''}\n\n"

                await update.message.reply_text(
                    options_text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Error al generar ejemplos")

        except ImportError:
            await update.message.reply_text(
                "❌ Error: No se puede procesar audio. Falta configuración de Gemini AI."
            )
        except Exception as transcribe_error:
            await update.message.reply_text(
                f"❌ Error al transcribir audio: {str(transcribe_error)}"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error al procesar audio: {str(e)}")


def setup_bot_application():
    """Configura la aplicación del bot con todos los handlers"""
    if not BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN no configurado en .env")
        return None

    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sync", sync_command))
    application.add_handler(CommandHandler("disconnect", disconnect_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("ejemplo", example_command))
    application.add_handler(CommandHandler("pregunta", question_command))
    application.add_handler(CommandHandler("analogia", analogy_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    return application


def run_bot_polling():
    """
    MODO POLLING (Solo para desarrollo/testing local)
    NO usar en producción - requiere proceso 24/7
    """
    application = setup_bot_application()
    if not application:
        return

    print("🤖 Bot de Telegram iniciado en modo POLLING (desarrollo)...")
    print("⚠️  ADVERTENCIA: Este modo NO es apropiado para producción")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    # Solo para testing local
    run_bot_polling()
