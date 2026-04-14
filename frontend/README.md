# Frontend - Sistema de Asistencia al Profesor

Sistema de asistencia basado en IA para profesores. Proyecto 3 - PDS 2025.

## Stack Tecnológico

- **React 19** - Framework principal
- **React Router DOM** - Enrutamiento
- **Vite** - Build tool
- **Tailwind CSS** (preparado) - Estilos
- **Lucide React** - Iconos
- **Firebase** - Autenticación (preparado)
- **Axios** - Cliente HTTP

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/          # Componentes UI reutilizables
│   │       ├── button.jsx
│   │       ├── card.jsx
│   │       ├── input.jsx
│   │       ├── alert.jsx
│   │       ├── badge.jsx
│   │       ├── separator.jsx
│   │       ├── label.jsx
│   │       ├── textarea.jsx
│   │       ├── select.jsx
│   │       └── tabs.jsx
│   ├── pages/           # Páginas principales
│   │   ├── AuthPage.jsx
│   │   ├── HomePage.jsx
│   │   ├── CreateClassPage.jsx
│   │   ├── ClassDetailPage.jsx
│   │   ├── PresentationViewPage.jsx
│   │   └── InstanceReportPage.jsx
│   ├── contexts/        # Contextos de React
│   │   └── AuthContext.jsx
│   ├── lib/            # Utilidades y configuraciones
│   │   └── firebase.js
│   ├── App.jsx         # Componente principal
│   └── main.jsx        # Punto de entrada
└── package.json
```

## Páginas Implementadas (Parcial 2)

### 1. AuthPage (`/auth`)
- Login con Google y email/password
- Registro de nuevos usuarios
- Diseño responsive con validaciones

### 2. HomePage (`/`)
- Lista de todas las clases creadas
- Búsqueda por título/asignatura
- Estadísticas generales
- Acceso rápido a crear/iniciar clases

### 3. CreateClassPage (`/classes/create`)
- Formulario para crear nueva clase
- Upload de presentación (PPTX/PDF)
- Validación de archivos (max 50MB)
- Campos: título, asignatura, nivel, descripción

### 4. ClassDetailPage (`/classes/:classId`)
- Información detallada de la clase
- Historial de instancias realizadas
- Estadísticas de uso
- Acciones: iniciar, editar, eliminar, descargar

### 5. PresentationViewPage (`/classes/:classId/start`)
- Visor de presentación en pantalla completa
- Navegación entre diapositivas (teclado/botones)
- Código de sincronización con control móvil
- Timer de sesión
- Vista de miniaturas
- Barra de progreso

### 6. InstanceReportPage (`/classes/:classId/instances/:instanceId`)
- Reporte completo de una instancia de clase
- Duración y estadísticas
- Flujo de navegación de diapositivas
- Tiempo en cada diapositiva (gráficos)
- Contenido generado con IA (ejemplos y preguntas)
- Muestra todas las opciones generadas y la seleccionada

## Instalación

1. **Instalar dependencias**:
```bash
npm install
```

2. **Iniciar servidor de desarrollo**:
```bash
npm run dev
```

3. **Build para producción**:
```bash
npm run build
```

## Endpoints del Backend (Por implementar)

### Autenticación
- `POST /api/auth/login` - Login con email/password
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/google` - Login con Google
- `GET /api/auth/me` - Obtener usuario actual

### Clases
- `GET /api/classes` - Lista de clases del usuario
- `POST /api/classes` - Crear nueva clase (multipart/form-data)
- `GET /api/classes/:id` - Detalle de clase
- `PUT /api/classes/:id` - Actualizar clase
- `DELETE /api/classes/:id` - Eliminar clase

### Instancias
- `POST /api/classes/:id/instances` - Iniciar nueva instancia
- `GET /api/classes/:id/instances` - Lista de instancias
- `GET /api/classes/:id/instances/:instanceId` - Detalle de instancia
- `PUT /api/classes/:id/instances/:instanceId` - Actualizar instancia

### Presentaciones
- `GET /api/presentations/:id/slides` - Obtener slides convertidas
- `POST /api/presentations/:id/generate-example` - Generar ejemplo con IA
- `POST /api/presentations/:id/generate-question` - Generar pregunta con IA

### Control/Sincronización
- `POST /api/sync/pair` - Sincronizar control con presentación
- `POST /api/sync/:code/command` - Enviar comando (next, prev, etc.)

## Características Implementadas

### Parcial 2 (27 octubre)
- ✅ Crear una clase (Plataforma Web)
- ✅ Iniciar una clase (Plataforma Web)
- ✅ Sincronizar control con plataforma (UI preparada)
- ✅ Control de la presentación (UI con navegación)

### Funcionalidades Adicionales
- ✅ Sistema de reporte detallado de instancias
- ✅ Vista previa de flujo de diapositivas
- ✅ Estadísticas y gráficos de tiempo
- ✅ UI completa con componentes reutilizables

## Tareas Pendientes (Backend)

- [ ] Implementar API REST con Flask
- [ ] Configurar Firebase Authentication
- [ ] Implementar conversión PPTX → PNG
- [ ] Integrar con LLM (OpenAI/Claude/Gemini)
- [ ] Implementar bot de Telegram
- [ ] WebSockets para sincronización en tiempo real
- [ ] Base de datos PostgreSQL

## Notas de Desarrollo

- **Mock Data**: Todas las páginas usan datos mock para desarrollo
- **Rutas**: No están protegidas aún (pendiente AuthContext completo)
- **Componentes UI**: Sistema de diseño básico implementado
- **Responsive**: Todas las páginas son responsive
- **Navegación**: Usa React Router DOM v6

## Configuración de Alias

El proyecto usa `@` como alias para `./src`:
```javascript
import { Button } from '@/components/ui/button';
```

Configurado en `vite.config.js`.

## Próximos Pasos (Parcial 3)

1. Integrar Firebase para autenticación real
2. Conectar con backend Flask
3. Implementar generación de ejemplos con IA
4. Proteger rutas con AuthContext
5. WebSocket para sincronización en tiempo real

---

**Universidad de los Andes - PDS 2025**
