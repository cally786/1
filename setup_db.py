from app import app, db
from app.models.models import User, Equipment, Category, Transaction, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    with app.app_context():
        # Crear todas las tablas
        db.create_all()

        # Crear categorías iniciales si no existen
        categories = [
            {'name': 'Router', 'description': 'Equipos de enrutamiento de red'},
            {'name': 'Switch', 'description': 'Equipos de conmutación de red'},
            {'name': 'Modem', 'description': 'Módems y equipos de conexión'},
            {'name': 'Antena', 'description': 'Antenas y equipos de transmisión'},
            {'name': 'Cable', 'description': 'Cables y conectores'},
            {'name': 'Conector', 'description': 'Conectores y adaptadores'},
            {'name': 'Herramienta', 'description': 'Herramientas y equipos de trabajo'},
            {'name': 'Otro', 'description': 'Otros equipos y materiales'}
        ]

        for cat_data in categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                category = Category(**cat_data)
                db.session.add(category)

        # Crear usuario administrador si no existe
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)

        try:
            db.session.commit()
            print("Base de datos inicializada correctamente.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al inicializar la base de datos: {str(e)}")

if __name__ == '__main__':
    init_db()
