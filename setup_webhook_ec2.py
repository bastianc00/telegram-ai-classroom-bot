#!/usr/bin/env python3
"""
Script para configurar webhook de Telegram en EC2

Uso:
    python setup_webhook_ec2.py

Asegúrate de tener configuradas las variables de entorno:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_WEBHOOK_SECRET (opcional pero recomendado)
"""
import requests
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET = os.getenv('TELEGRAM_WEBHOOK_SECRET', '')

# URL del backend (configurar via variable de entorno BACKEND_URL)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
WEBHOOK_URL = f"{BACKEND_URL}/api/telegram/webhook"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Imprime el header del script"""
    print("\n" + "="*60)
    print(f"{Colors.BOLD}🤖 Configuración de Webhook de Telegram{Colors.END}")
    print("="*60 + "\n")

def validate_config():
    """Valida que la configuración esté completa"""
    print(f"{Colors.BLUE}📋 Validando configuración...{Colors.END}")

    if not BOT_TOKEN:
        print(f"{Colors.RED}❌ ERROR: TELEGRAM_BOT_TOKEN no configurado{Colors.END}")
        print("   Configura la variable de entorno o agrégala al .env")
        return False

    if not WEBHOOK_SECRET:
        print(f"{Colors.YELLOW}⚠️  ADVERTENCIA: TELEGRAM_WEBHOOK_SECRET no configurado{Colors.END}")
        print("   Se recomienda configurar un secret token para seguridad")

    print(f"{Colors.GREEN}✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}{Colors.END}")
    print(f"{Colors.GREEN}✅ Backend URL: {BACKEND_URL}{Colors.END}")
    print(f"{Colors.GREEN}✅ Webhook URL: {WEBHOOK_URL}{Colors.END}\n")

    return True

def delete_webhook():
    """Elimina el webhook actual (útil para limpiar)"""
    print(f"{Colors.BLUE}🗑️  Eliminando webhook anterior...{Colors.END}")

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
            json={"drop_pending_updates": True}
        )

        result = response.json()

        if result.get('ok'):
            print(f"{Colors.GREEN}✅ Webhook anterior eliminado{Colors.END}\n")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  No había webhook configurado{Colors.END}\n")
            return True

    except Exception as e:
        print(f"{Colors.RED}❌ Error eliminando webhook: {e}{Colors.END}\n")
        return False

def setup_webhook():
    """Configura el webhook en Telegram"""
    print(f"{Colors.BLUE}🔧 Configurando nuevo webhook...{Colors.END}")

    # Preparar parámetros
    params = {
        "url": WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query", "edited_message"],
        "drop_pending_updates": True,
        "max_connections": 40
    }

    # Agregar secret token si está configurado
    if WEBHOOK_SECRET:
        params["secret_token"] = WEBHOOK_SECRET
        print(f"   🔐 Secret token configurado")

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json=params
        )

        result = response.json()

        if result.get('ok'):
            print(f"{Colors.GREEN}✅ Webhook configurado exitosamente!{Colors.END}")
            print(f"   URL: {WEBHOOK_URL}\n")
            return True
        else:
            print(f"{Colors.RED}❌ Error configurando webhook:{Colors.END}")
            print(f"   {result.get('description')}\n")
            return False

    except Exception as e:
        print(f"{Colors.RED}❌ Error en la petición: {e}{Colors.END}\n")
        return False

def verify_webhook():
    """Verifica la configuración del webhook"""
    print(f"{Colors.BLUE}🔍 Verificando webhook...{Colors.END}")

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        )

        info = response.json()

        if not info.get('ok'):
            print(f"{Colors.RED}❌ Error obteniendo info: {info.get('description')}{Colors.END}")
            return False

        result = info['result']

        # Mostrar información
        print(f"\n{Colors.BOLD}Información del Webhook:{Colors.END}")
        print(f"   URL: {result.get('url')}")
        print(f"   Custom certificate: {result.get('has_custom_certificate')}")
        print(f"   Pending updates: {result.get('pending_update_count', 0)}")
        print(f"   Max connections: {result.get('max_connections', 40)}")
        print(f"   Allowed updates: {', '.join(result.get('allowed_updates', []))}")

        # Verificar si hay errores
        if result.get('last_error_date'):
            print(f"\n{Colors.YELLOW}⚠️  Último error:{Colors.END}")
            print(f"   Fecha: {result.get('last_error_date')}")
            print(f"   Mensaje: {result.get('last_error_message')}")
            return False
        else:
            print(f"\n{Colors.GREEN}✅ Sin errores recientes{Colors.END}")

        # Verificar URL correcta
        if result.get('url') != WEBHOOK_URL:
            print(f"\n{Colors.YELLOW}⚠️  La URL configurada no coincide:{Colors.END}")
            print(f"   Esperada: {WEBHOOK_URL}")
            print(f"   Actual: {result.get('url')}")
            return False

        return True

    except Exception as e:
        print(f"{Colors.RED}❌ Error verificando webhook: {e}{Colors.END}")
        return False

def test_webhook():
    """Hace un test básico al endpoint del webhook"""
    print(f"\n{Colors.BLUE}🧪 Probando endpoint del webhook...{Colors.END}")

    try:
        # Hacer request al health check del backend
        health_url = f"{BACKEND_URL}/health"
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Backend respondiendo correctamente{Colors.END}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Backend responde pero con error:{Colors.END}")
            print(f"   Status: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}❌ Timeout - Backend no responde (puede estar iniciando){Colors.END}")
        print(f"   Espera unos minutos y verifica en Render Dashboard")
        return False

    except Exception as e:
        print(f"{Colors.RED}❌ Error probando backend: {e}{Colors.END}")
        return False

def print_next_steps():
    """Imprime los siguientes pasos"""
    print(f"\n{Colors.BOLD}📱 Próximos Pasos:{Colors.END}")
    print(f"\n1. Abre Telegram y busca tu bot")
    print(f"2. Envía: {Colors.BOLD}/start{Colors.END}")
    print(f"3. Verifica que el bot responde")
    print(f"\n4. Para ver logs en Render:")
    print(f"   Dashboard → Backend → Logs")
    print(f"   Busca: {Colors.BLUE}POST /api/telegram/webhook{Colors.END}")
    print(f"\n5. Si el bot no responde, verifica:")
    print(f"   • Backend está corriendo en Render")
    print(f"   • Variables de entorno configuradas")
    print(f"   • URL del webhook es accesible (HTTPS)")

def main():
    """Función principal"""
    print_header()

    # Validar configuración
    if not validate_config():
        sys.exit(1)

    # Confirmar con usuario
    print(f"{Colors.YELLOW}¿Deseas configurar el webhook? (s/n):{Colors.END} ", end='')
    confirm = input().lower()

    if confirm != 's':
        print(f"\n{Colors.RED}❌ Operación cancelada{Colors.END}")
        sys.exit(0)

    print()

    # Proceso de configuración
    steps_ok = True

    # 1. Eliminar webhook anterior
    if not delete_webhook():
        steps_ok = False

    # 2. Configurar nuevo webhook
    if steps_ok and not setup_webhook():
        steps_ok = False

    # 3. Verificar webhook
    if steps_ok and not verify_webhook():
        steps_ok = False

    # 4. Probar backend
    if steps_ok:
        test_webhook()

    # Resumen final
    print("\n" + "="*60)
    if steps_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE{Colors.END}")
        print_next_steps()
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ CONFIGURACIÓN INCOMPLETA{Colors.END}")
        print(f"\n{Colors.YELLOW}Verifica los errores anteriores y vuelve a intentar{Colors.END}")

    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Operación cancelada por el usuario{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.END}\n")
        sys.exit(1)
