from app import app, db
from app.models.models import Equipment, Transaction, User, Category
from datetime import datetime

def test_status_changes():
    with app.app_context():
        # 1. Crear datos de prueba
        print("\n1. Creando datos de prueba...")
        
        # Crear usuario admin
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = User(email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Crear usuario normal
        user = User.query.filter_by(email='user@test.com').first()
        if not user:
            user = User(email='user@test.com', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
        
        # Crear categoría
        category = Category.query.filter_by(name='Test Category').first()
        if not category:
            category = Category(name='Test Category')
            db.session.add(category)
        
        db.session.commit()
        
        # 2. Crear equipo
        print("\n2. Creando equipo...")
        equipment = Equipment(
            name='Test Equipment',
            description='Test Description',
            quantity=5,
            available_quantity=5,
            category_id=category.id,
            creator_id=user.id,
            status='En revisión'
        )
        db.session.add(equipment)
        db.session.commit()
        print(f"Estado inicial: {equipment.status}, Cantidad: {equipment.available_quantity}")
        
        # 3. Publicar equipo
        print("\n3. Publicando equipo...")
        equipment.status = 'Publicado'
        db.session.commit()
        print(f"Estado después de publicar: {equipment.status}, Cantidad: {equipment.available_quantity}")
        
        # 4. Crear transacción que reduzca el stock a 0
        print("\n4. Creando transacción que agota el stock...")
        transaction = Transaction(
            equipment_id=equipment.id,
            buyer_id=admin.id,
            seller_id=user.id,
            quantity=5,
            unit_price=100,
            status='Pendiente'
        )
        db.session.add(transaction)
        equipment.available_quantity = 0
        equipment.update_status_based_on_quantity()
        print(f"Estado después de agotar stock: {equipment.status}, Cantidad: {equipment.available_quantity}")
        
        # 5. Rechazar la transacción (debe volver a Publicado)
        print("\n5. Rechazando transacción...")
        transaction.status = 'Rechazado'
        equipment.process_transaction_completion(transaction)
        print(f"Estado después de rechazar transacción: {equipment.status}, Cantidad: {equipment.available_quantity}")
        
        # 6. Crear y completar una nueva transacción
        print("\n6. Creando y completando nueva transacción...")
        new_transaction = Transaction(
            equipment_id=equipment.id,
            buyer_id=admin.id,
            seller_id=user.id,
            quantity=5,
            unit_price=100,
            status='Completado'
        )
        db.session.add(new_transaction)
        equipment.process_transaction_completion(new_transaction)
        print(f"Estado final después de completar transacción: {equipment.status}, Cantidad: {equipment.available_quantity}")

if __name__ == '__main__':
    test_status_changes()
