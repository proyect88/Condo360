"""Script para poblar la base de datos con datos iniciales"""

import sys
import os

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"
    ),
)

from app import create_app, db
from app.models.user import User
from app.models.service import Service
from app.models.testimonial import Testimonial
from app.models.ticket import Ticket
from app.models.client import Client


def seed_database():
    app = create_app()
    with app.app_context():
        # Respaldo para desarrollo: crea tablas si no se ejecutaron migraciones
        db.create_all()
        print("Iniciando siembra de datos...")

        # 1. Crear usuario admin
        admin = User.query.filter_by(email=app.config["ADMIN_EMAIL"]).first()
        if not admin:
            admin = User(
                email=app.config["ADMIN_EMAIL"],
                full_name="Administrador",
                role="admin",
                is_active=True,
            )
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            print(" Usuario admin creado")
            if app.config["ADMIN_PASSWORD"] == "Admin123456!":
                print(
                    " ADVERTENCIA: estas usando la contrasena de fabrica. "
                    "Define ADMIN_PASSWORD en .env antes de produccion."
                )

        # 2. Crear servicios
        services_data = [
            {
                "name": "Albañilería Profesional",
                "slug": "albanileria",
                "category": "albanileria",
                "description": "Servicios completos de albañilería: reparación de muros, fisuras, revestimientos, impermeabilizaciones y más. Trabajamos con materiales de primera calidad y garantizamos resultados duraderos.",
                "short_description": "Reparación y mantenimiento de estructuras, muros y revestimientos",
                "icon": "fa-helmet-safety",
                "price_from": 150000,
                "features": [
                    "Reparación de muros",
                    "Impermeabilización",
                    "Revestimientos",
                    "Pisos",
                    "Acabados",
                ],
                "is_active": True,
                "is_featured": True,
                "order": 1,
            },
            {
                "name": "Plomería Integral",
                "slug": "plomeria",
                "category": "plomeria",
                "description": "Instalación y reparación de sistemas de agua potable, alcantarillado, calefacción y grifería. Servicio técnico especializado con garantía.",
                "short_description": "Sistemas de agua, desagües, calefacción y grifería",
                "icon": "fa-wrench",
                "price_from": 80000,
                "features": [
                    "Reparación de cañerías",
                    "Cambio de grifería",
                    "Desagües",
                    "Calefones",
                    "Tanques de agua",
                ],
                "is_active": True,
                "is_featured": True,
                "order": 2,
            },
            {
                "name": "Electricidad Residencial",
                "slug": "electricidad",
                "category": "electricidad",
                "description": "Instalaciones eléctricas, tableros, iluminación, y mantenimiento de sistemas eléctricos en condominios. Seguridad y eficiencia energética.",
                "short_description": "Instalaciones, tableros, iluminación y seguridad eléctrica",
                "icon": "fa-bolt",
                "price_from": 90000,
                "features": [
                    "Instalaciones eléctricas",
                    "Tableros",
                    "Iluminación",
                    "Sistemas de seguridad",
                    "Ahorro energético",
                ],
                "is_active": True,
                "is_featured": True,
                "order": 3,
            },
            {
                "name": "Jardinería y Paisajismo",
                "slug": "jardineria",
                "category": "jardineria",
                "description": "Diseño, mantenimiento y recuperación de áreas verdes en condominios. Paisajismo profesional que realza la belleza de tus espacios comunes.",
                "short_description": "Diseño, mantenimiento y recuperación de áreas verdes",
                "icon": "fa-leaf",
                "price_from": 120000,
                "features": [
                    "Diseño de jardines",
                    "Mantenimiento",
                    "Poda",
                    "Riego automático",
                    "Control de plagas",
                ],
                "is_active": True,
                "is_featured": True,
                "order": 4,
            },
            {
                "name": "Mantenimiento de Ascensores",
                "slug": "ascensores",
                "category": "ascensores",
                "description": "Mantenimiento preventivo, correctivo y modernización de ascensores. Certificaciones y cumplimiento normativo vigente.",
                "short_description": "Preventivo, correctivo y modernización de ascensores",
                "icon": "fa-elevator",
                "price_from": 200000,
                "features": [
                    "Mantenimiento preventivo",
                    "Reparaciones",
                    "Modernización",
                    "Certificaciones",
                    "24/7 Emergencia",
                ],
                "is_active": True,
                "is_featured": True,
                "order": 5,
            },
            {
                "name": "Gestión de Mantenimiento",
                "slug": "gestion-mantenimiento",
                "category": "gestion",
                "description": "Planificación y gestión integral del mantenimiento de tu condominio. Reportes detallados y seguimiento personalizado.",
                "short_description": "Planificación, gestión y reportes de mantenimiento",
                "icon": "fa-clipboard-check",
                "price_from": 180000,
                "features": [
                    "Planificación",
                    "Presupuestos",
                    "Supervisión",
                    "Reportes",
                    "Soporte continuo",
                ],
                "is_active": True,
                "is_featured": False,
                "order": 6,
            },
        ]

        for data in services_data:
            service = Service.query.filter_by(slug=data["slug"]).first()
            if not service:
                service = Service(**data)
                db.session.add(service)
        print(" Servicios creados")

        # 3. Crear clientes
        clients_data = [
            {
                "name": "María González",
                "email": "maria@residencialbosques.cl",
                "phone": "+56912345678",
                "condominium_name": "Residencial Los Bosques",
                "address": "Av. Los Bosques 123",
                "city": "Santiago",
                "position": "Presidenta Junta de Vecinos",
                "units_count": 45,
            },
            {
                "name": "Carlos Rodríguez",
                "email": "carlos@torresdelparque.cl",
                "phone": "+56987654321",
                "condominium_name": "Torres del Parque",
                "address": "Calle Parque 456",
                "city": "Santiago",
                "position": "Administrador",
                "units_count": 120,
            },
            {
                "name": "Ana Martínez",
                "email": "ana@viveronorte.cl",
                "phone": "+56945678912",
                "condominium_name": "Vivero del Norte",
                "address": "Av. Norte 789",
                "city": "Santiago",
                "position": "Directora",
                "units_count": 60,
            },
        ]

        for data in clients_data:
            client = Client.query.filter_by(email=data["email"]).first()
            if not client:
                client = Client(**data)
                db.session.add(client)
        print(" Clientes creados")

        # 4. Crear testimonios
        testimonials_data = [
            {
                "client_name": "María González",
                "client_position": "Presidenta Junta de Vecinos",
                "condominium_name": "Residencial Los Bosques",
                "content": "Desde que contratamos a Condo Services 360, la gestión de mantenimiento ha sido excelente. Los técnicos son profesionales, puntuales y el trabajo de albañilería quedó impecable. Muy recomendados.",
                "rating": 5,
                "service_name": "Albañilería",
                "service_id": 1,
                "is_approved": True,
                "is_featured": True,
            },
            {
                "client_name": "Carlos Rodríguez",
                "client_position": "Administrador",
                "condominium_name": "Torres del Parque",
                "content": "El servicio de plomería fue excepcional. Resolvieron un problema de fugas que nos afectaba hace meses en tiempo récord. El equipo es muy profesional y el precio es justo.",
                "rating": 5,
                "service_name": "Plomería",
                "service_id": 2,
                "is_approved": True,
                "is_featured": True,
            },
            {
                "client_name": "Ana Martínez",
                "client_position": "Directora",
                "condominium_name": "Vivero del Norte",
                "content": "La jardinería quedó impecable. Transformaron completamente nuestras áreas comunes. El servicio de mantenimiento de áreas verdes es de primera calidad.",
                "rating": 5,
                "service_name": "Jardinería",
                "service_id": 4,
                "is_approved": True,
                "is_featured": False,
            },
            {
                "client_name": "Pedro Soto",
                "client_position": "Presidente",
                "condominium_name": "Edificio Central",
                "content": "Excelente servicio de mantenimiento de ascensores. Cumplen con todas las normativas y el mantenimiento preventivo ha prolongado la vida útil de nuestros ascensores.",
                "rating": 4,
                "service_name": "Ascensores",
                "service_id": 5,
                "is_approved": True,
                "is_featured": False,
            },
        ]

        for data in testimonials_data:
            testimonial = Testimonial.query.filter_by(
                client_name=data["client_name"], content=data["content"]
            ).first()
            if not testimonial:
                testimonial = Testimonial(**data)
                db.session.add(testimonial)
        print(" Testimonios creados")

        # 4b. Galeria demo: 10 imagenes por servicio (cintillo de trabajos)
        from app.models.service_image import ServiceImage

        for service in Service.query.all():
            existentes = service.gallery_images.count()
            if existentes > 0:
                continue
            for n in range(1, 11):
                db.session.add(
                    ServiceImage(
                        service_id=service.id,
                        image_path=f"uploads/servicios/demo-{n}.jpg",
                        caption=f"Trabajo realizado {n}",
                        order=n,
                    )
                )
        print(" Galerias de servicios creadas (10 imagenes demo c/u)")

        # 5. Crear tickets de ejemplo
        tickets_data = [
            {
                "client_name": "María González",
                "client_email": "maria@residencialbosques.cl",
                "client_phone": "+56912345678",
                "condominium_name": "Residencial Los Bosques",
                "service_type": "albanileria",
                "description": "Se requiere reparación de fisuras en estacionamiento subterráneo. Hay humedad y algunas filtraciones.",
                "urgency": "medium",
                "status": "in_progress",
            },
            {
                "client_name": "Carlos Rodríguez",
                "client_email": "carlos@torresdelparque.cl",
                "client_phone": "+56987654321",
                "condominium_name": "Torres del Parque",
                "service_type": "plomeria",
                "description": "Fuga de agua en el sistema de riego del jardín central. Necesita reparación urgente.",
                "urgency": "high",
                "status": "new",
            },
        ]

        for data in tickets_data:
            ticket = Ticket(**data)
            db.session.add(ticket)
        print(" Tickets de ejemplo creados")

        # 6. Commit final
        db.session.commit()
        print(" ¡Base de datos poblada exitosamente!")


if __name__ == "__main__":
    seed_database()
