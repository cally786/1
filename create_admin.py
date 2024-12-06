from app import app, db
from app.models.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Crear un nuevo usuario admin
        new_admin = User(
            email='admin2@admin.com',
            password_hash=generate_password_hash('Admin123!'),
            is_admin=True,
            first_name='Admin',
            last_name='Dos',
            company='Empresa',
            phone='123456789'
        )
        
        try:
            db.session.add(new_admin)
            db.session.commit()
            print("Usuario admin creado exitosamente!")
            print("Credenciales:")
            print("Email: admin2@admin.com")
            print("Contraseña: Admin123!")
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear el usuario admin: {str(e)}")

if __name__ == '__main__':
    create_admin_user()
