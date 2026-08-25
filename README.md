# Condo Services 360 - Plataforma Integral para Condominios

## Descripcion

Plataforma web completa para la gestion de servicios de mantenimiento en condominios. Incluye albanileria, plomeria, electricidad, jardineria, mantenimiento de ascensores y mas.

## Caracteristicas Principales

- Landing page moderna con diseno 2026
- Panel de administracion completo
- PWA (Progressive Web App) con soporte offline
- Diagnostico interactivo para condominios
- Sistema de tickets y gestion de solicitudes
- CRUD de servicios, testimonios y clientes
- API RESTful para integraciones
- Diseno responsive y accesible
- Notificaciones push
- Sistema de autenticacion

## Tecnologias Utilizadas

### Backend
- Python 3.11+
- Flask 3.0+
- SQLAlchemy 3.1+
- Flask-Login 0.6+
- Flask-WTF 1.2+
- Flask-Migrate 4.0+

### Frontend
- HTML5, CSS3 (Diseno 2026)
- JavaScript Vanilla
- PWA (Service Worker, Manifest)
- FontAwesome 6.5+


### Infraestructura
- Docker & Docker Compose
- Gunicorn
- Nginx


## Estructura del Proyecto

```
condo-services-360/
├── backend/          # Codigo Python Flask
├── frontend/         # Assets estaticos
├── scripts/          # Scripts de utilidad
├── tests/            # Tests
└── migrations/       # Migraciones de BD
```

Nota: los archivos `manifest.json` y `sw.js` viven en la raiz de `frontend/` y se sirven en las rutas `/manifest.json` y `/sw.js` desde la factory de Flask.


## PWA

La aplicacion es instalable como PWA:

- Instalable en dispositivos moviles
- Funcionalidad offline
- Notificaciones push
- Actualizaciones automaticas





