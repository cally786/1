from app import app, db
from app.models.models import User, Category
from werkzeug.security import generate_password_hash

def init_admin():
    with app.app_context():
        # Crear usuario admin si no existe
        admin = User.query.filter_by(email='admin@admin.com').first()
        if not admin:
            admin = User(
                email='admin@admin.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            
        # Crear categoría de prueba si no existe
        test_category = Category.query.filter_by(name='Test').first()
        if not test_category:
            test_category = Category(
                name='Test',
                description='Categoría para pruebas'
            )
            db.session.add(test_category)
            
        db.session.commit()
        print("Usuario admin y categoría de prueba creados exitosamente")

if __name__ == '__main__':
    init_admin()
