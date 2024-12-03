from app import app, db
from app.models.models import Equipment

def check_equipment_status():
    with app.app_context():
        # Buscar todos los equipos con cantidad 0
        zero_quantity_equipment = Equipment.query.filter_by(available_quantity=0).all()
        
        print("\nEquipos con cantidad 0:")
        print("-" * 50)
        for equipment in zero_quantity_equipment:
            print(f"ID: {equipment.id}")
            print(f"Nombre: {equipment.name}")
            print(f"Estado actual: {equipment.status}")
            print(f"Cantidad disponible: {equipment.available_quantity}")
            print("-" * 50)

if __name__ == '__main__':
    check_equipment_status()
