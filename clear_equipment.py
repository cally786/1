from app import app, db
from app.models.models import Equipment, Transaction

def clear_equipment():
    with app.app_context():
        # Primero borramos las transacciones relacionadas
        Transaction.query.delete()
        # Luego borramos los equipos
        Equipment.query.delete()
        # Guardamos los cambios
        db.session.commit()
        print("Se han borrado todos los equipos y sus transacciones relacionadas.")

if __name__ == '__main__':
    clear_equipment()
