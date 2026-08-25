from app.models.service import Service
from app import db
import logging

logger = logging.getLogger(__name__)


class ServiceManager:
    """Gestor de servicios"""

    @staticmethod
    def get_all_active():
        """Obtener todos los servicios activos"""
        return Service.query.filter_by(is_active=True).order_by(Service.order).all()

    @staticmethod
    def get_by_category(category):
        """Obtener servicios por categoría"""
        return (
            Service.query.filter_by(category=category, is_active=True)
            .order_by(Service.order)
            .all()
        )

    @staticmethod
    def get_featured():
        """Obtener servicios destacados"""
        return (
            Service.query.filter_by(is_active=True, is_featured=True)
            .order_by(Service.order)
            .all()
        )

    @staticmethod
    def create_service(data):
        """Crear un nuevo servicio"""
        try:
            service = Service(**data)
            db.session.add(service)
            db.session.commit()
            logger.info(f"Servicio creado: {service.name}")
            return service
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear servicio: {str(e)}")
            raise

    @staticmethod
    def update_service(service_id, data):
        """Actualizar un servicio"""
        service = Service.query.get(service_id)
        if not service:
            raise ValueError("Servicio no encontrado")

        try:
            for key, value in data.items():
                if hasattr(service, key):
                    setattr(service, key, value)
            db.session.commit()
            logger.info(f"Servicio actualizado: {service.name}")
            return service
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar servicio: {str(e)}")
            raise

    @staticmethod
    def delete_service(service_id):
        """Eliminar un servicio"""
        service = Service.query.get(service_id)
        if not service:
            raise ValueError("Servicio no encontrado")

        try:
            db.session.delete(service)
            db.session.commit()
            logger.info(f"Servicio eliminado: {service.name}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al eliminar servicio: {str(e)}")
            raise

    @staticmethod
    def get_categories():
        """Obtener todas las categorías"""
        categories = db.session.query(Service.category).distinct().all()
        return [c[0] for c in categories if c[0]]

    @staticmethod
    def get_service_by_slug(slug):
        """Obtener servicio por slug"""
        return Service.query.filter_by(slug=slug, is_active=True).first()
