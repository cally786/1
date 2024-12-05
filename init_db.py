from app import app, db
from app.models.models import User
from werkzeug.security import generate_password_hash
import os

# Eliminar base de datos existente
db_path = os.path.join('instance', 'database.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print("Base de datos existente eliminada")

with app.app_context():
    # Crear tablas
    db.create_all()
    print("Tablas creadas exitosamente")
    
    # Crear usuario admin
    admin = User(
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Usuario admin creado exitosamente")
