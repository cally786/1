from app import app, db
from app.models.models import Equipment

def fix_equipment_status():
    with app.app_context():
        # Buscar todos los equipos con cantidad 0 y estado Publicado
        equipment_to_fix = Equipment.query.filter_by(
            available_quantity=0, 
            status='Publicado'
        ).all()
        
        print(f"\nEncontramos {len(equipment_to_fix)} equipos para actualizar")
        
        for equipment in equipment_to_fix:
            print(f"\nActualizando equipo ID: {equipment.id}")
            print(f"Nombre: {equipment.name}")
            print(f"Estado anterior: {equipment.status}")
            
            equipment.status = 'Vendido'
            print(f"Nuevo estado: {equipment.status}")
        
        db.session.commit()
        print("\nActualización completada")

if __name__ == '__main__':
    fix_equipment_status()
