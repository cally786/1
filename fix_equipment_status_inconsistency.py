from app import app, db
from app.models.models import Equipment
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_equipment_status():
    with app.app_context():
        try:
            # Buscar equipos con cantidad 0 que estén en estado Publicado
            equipments = Equipment.query.filter_by(available_quantity=0, status='Publicado').all()
            
            count = 0
            for equipment in equipments:
                logger.info(f"Equipo encontrado: {equipment.name} (ID: {equipment.id})")
                logger.info(f"Estado anterior: {equipment.status}, Cantidad: {equipment.available_quantity}")
                
                # Cambiar el estado a Agotado
                equipment.status = 'Agotado'
                count += 1
                
                logger.info(f"Nuevo estado: {equipment.status}")
                logger.info("-------------------")
            
            if count > 0:
                db.session.commit()
                logger.info(f"Se actualizaron {count} equipos de Publicado a Agotado")
            else:
                logger.info("No se encontraron equipos con inconsistencias")

        except Exception as e:
            logger.error(f"Error al corregir estados: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    fix_equipment_status()
