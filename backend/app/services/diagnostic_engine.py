import logging
from app.models.service import Service

logger = logging.getLogger(__name__)


class DiagnosticEngine:
    """Motor de diagnóstico para condominios"""

    def __init__(self):
        self.issue_weights = {
            "fugas_agua": 8,
            "problemas_electricos": 7,
            "estructural": 9,
            "ascensor": 7,
            "humedad": 5,
            "jardineria": 3,
            "cosmetico": 2,
            "seguridad": 8,
            "saneamiento": 6,
        }

        self.issue_to_service = {
            "fugas_agua": "plomeria",
            "problemas_electricos": "electricidad",
            "estructural": "albanileria",
            "ascensor": "ascensores",
            "humedad": "albanileria",
            "jardineria": "jardineria",
            "seguridad": "electricidad",
            "saneamiento": "plomeria",
        }

    def analyze(self, data):
        """Analizar datos y generar diagnóstico"""
        try:
            issues = data.get("issue_types", [])
            building_age = (
                int(data.get("building_age", 0)) if data.get("building_age") else 0
            )

            # Calcular puntaje de urgencia
            urgency_score = self._calculate_urgency(issues, building_age)

            # Determinar servicio recomendado
            recommended_service = self._recommend_service(issues)

            # Generar plan de acción
            action_plan = self._generate_action_plan(issues, urgency_score)

            return {
                "urgency_score": urgency_score,
                "recommended_service_id": (
                    recommended_service.id if recommended_service else None
                ),
                "recommended_service": (
                    recommended_service.name if recommended_service else None
                ),
                "action_plan": action_plan,
                "priority_areas": self._get_priority_areas(issues),
                "estimated_cost": self._estimate_cost(issues, building_age),
                "recommendations": self._get_recommendations(issues, building_age),
            }

        except Exception as e:
            logger.error(f"Error en diagnóstico: {str(e)}")
            return {"urgency_score": 5, "error": str(e)}

    def _calculate_urgency(self, issues, building_age):
        """Calcular puntaje de urgencia"""
        if not issues:
            return 3

        total_score = 0
        for issue in issues:
            total_score += self.issue_weights.get(issue, 3)

        # Ajustar por edad del edificio
        if building_age > 30:
            total_score *= 1.2
        elif building_age > 20:
            total_score *= 1.1

        avg_score = total_score / len(issues)
        return min(int(avg_score), 10)

    def _recommend_service(self, issues):
        """Recomendar servicio basado en los issues"""
        if not issues:
            return None

        # Contar ocurrencias por categoría
        category_counts = {}
        for issue in issues:
            category = self.issue_to_service.get(issue)
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

        if not category_counts:
            return None

        # Seleccionar la categoría más común
        top_category = max(category_counts, key=category_counts.get)

        # Buscar servicio activo de esa categoría
        service = Service.query.filter_by(category=top_category, is_active=True).first()
        return service

    def _generate_action_plan(self, issues, urgency_score):
        """Generar plan de acción"""
        if urgency_score >= 8:
            priority = "crítica"
            timeline = "Inmediata (24-48 horas)"
        elif urgency_score >= 6:
            priority = "alta"
            timeline = "Urgente (2-5 días)"
        elif urgency_score >= 4:
            priority = "media"
            timeline = "Programada (1-2 semanas)"
        else:
            priority = "baja"
            timeline = "Planificada (1 mes)"

        actions = []
        for issue in issues:
            action = self._get_action_for_issue(issue)
            if action:
                actions.append(action)

        return {"priority": priority, "timeline": timeline, "actions": actions[:5]}

    def _get_action_for_issue(self, issue):
        """Obtener acción específica para un issue"""
        actions = {
            "fugas_agua": "Revisar sistema de cañerías y reparar fugas detectadas",
            "problemas_electricos": "Inspeccionar tablero eléctrico y sistema de iluminación",
            "estructural": "Realizar evaluación estructural por ingeniero especializado",
            "ascensor": "Revisar sistema de ascensores y seguridad",
            "humedad": "Impermeabilizar zonas afectadas y mejorar ventilación",
            "jardineria": "Realizar mantenimiento de áreas verdes y poda",
            "seguridad": "Actualizar sistema de seguridad y cámaras",
            "saneamiento": "Revisar sistema de alcantarillado y saneamiento",
        }
        return actions.get(issue)

    def _get_priority_areas(self, issues):
        """Obtener áreas prioritarias"""
        if not issues:
            return []

        priority_map = {
            "fugas_agua": "Sistema de agua potable",
            "problemas_electricos": "Sistema eléctrico",
            "estructural": "Estructura del edificio",
            "ascensor": "Sistema de ascensores",
            "humedad": "Muros y techos",
            "jardineria": "Áreas verdes",
            "seguridad": "Seguridad del condominio",
            "saneamiento": "Sistema de alcantarillado",
        }

        areas = [priority_map.get(issue) for issue in issues if priority_map.get(issue)]
        return list(set(areas))

    def _estimate_cost(self, issues, building_age):
        """Estimar costo aproximado"""
        base_cost = 100000
        cost_per_issue = 50000

        total = base_cost + (len(issues) * cost_per_issue)

        # Ajustar por edad
        if building_age > 30:
            total *= 1.3
        elif building_age > 20:
            total *= 1.2

        # Ajustar por urgencia
        urgency = self._calculate_urgency(issues, building_age)
        if urgency >= 8:
            total *= 1.2

        return int(total)

    def _get_recommendations(self, issues, building_age):
        """Obtener recomendaciones adicionales"""
        recommendations = []

        if building_age > 25:
            recommendations.append("Considerar una inspección estructural completa")

        if "fugas_agua" in issues or "saneamiento" in issues:
            recommendations.append("Revisar cañerías principales de agua potable")

        if "problemas_electricos" in issues:
            recommendations.append("Verificar capacidad del sistema eléctrico")

        if "ascensor" in issues:
            recommendations.append(
                "Revisar mantenimiento de ascensores según normativa"
            )

        return recommendations[:3]
