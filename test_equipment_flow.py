from app import app, db
from app.models.models import User, Equipment, Transaction, Category
from datetime import datetime
import logging
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_db_state(equipment_id, expected_status=None, expected_quantity=None):
    """Verificar el estado actual en la base de datos"""
    # Forzar refresh desde la base de datos
    db.session.expire_all()
    equipment = Equipment.query.get(equipment_id)
    db.session.refresh(equipment)
    
    logger.info("\nEstado actual en la base de datos:")
    logger.info(f"ID: {equipment.id}")
    logger.info(f"Estado en DB: {equipment.status}")
    logger.info(f"Cantidad en DB: {equipment.available_quantity}")
    
    if expected_status:
        assert equipment.status == expected_status, f"Estado esperado: {expected_status}, Actual: {equipment.status}"
    if expected_quantity is not None:
        assert equipment.available_quantity == expected_quantity, f"Cantidad esperada: {expected_quantity}, Actual: {equipment.available_quantity}"
    
    return equipment

def setup_test_data():
    """Configurar datos iniciales para la prueba"""
    try:
        # Crear usuarios de prueba
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            logger.info("Usuario admin creado")

        seller = User.query.filter_by(username='vendedor').first()
        if not seller:
            seller = User(username='vendedor', is_admin=False)
            seller.set_password('vendedor123')
            db.session.add(seller)
            logger.info("Usuario vendedor creado")

        buyer = User.query.filter_by(username='comprador').first()
        if not buyer:
            buyer = User(username='comprador', is_admin=False)
            buyer.set_password('comprador123')
            db.session.add(buyer)
            logger.info("Usuario comprador creado")

        # Crear categoría de prueba
        category = Category.query.filter_by(name='Test Category').first()
        if not category:
            category = Category(name='Test Category')
            db.session.add(category)
            logger.info("Categoría de prueba creada")

        db.session.commit()
        return admin, seller, buyer, category

    except Exception as e:
        logger.error(f"Error en setup_test_data: {str(e)}")
        db.session.rollback()
        raise

def create_test_equipment(seller, category):
    """Crear equipo de prueba"""
    try:
        # Generar un número de serie único
        serial_number = f"TEST-{str(uuid.uuid4())[:8]}"
        
        equipment = Equipment(
            name='Equipo de Prueba',
            description='Descripción del equipo de prueba',
            quantity=5,
            available_quantity=5,
            category_id=category.id,
            creator_id=seller.id,
            company='Empresa Test',
            model='Modelo Test',
            serial_number=serial_number,
            unit_price=100.0,
            location='São Paulo',
            status='En revisión',
            created_at=datetime.utcnow()
        )
        db.session.add(equipment)
        db.session.commit()
        logger.info(f"Equipo creado: {equipment.name} (ID: {equipment.id}, Serial: {serial_number})")
        return equipment

    except Exception as e:
        logger.error(f"Error en create_test_equipment: {str(e)}")
        db.session.rollback()
        raise

def approve_and_publish_equipment(admin, equipment):
    """Aprobar y publicar equipo"""
    try:
        equipment.status = 'Publicado'
        db.session.commit()
        logger.info(f"Equipo publicado: {equipment.name} (ID: {equipment.id})")

    except Exception as e:
        logger.error(f"Error en approve_and_publish_equipment: {str(e)}")
        db.session.rollback()
        raise

def create_transaction(buyer, equipment):
    """Crear transacción de prueba"""
    try:
        # Verificar si hay suficiente cantidad disponible
        if equipment.available_quantity < 1:
            raise ValueError(f"No hay suficiente cantidad disponible. Disponible: {equipment.available_quantity}")

        transaction = Transaction(
            equipment_id=equipment.id,
            buyer_id=buyer.id,
            seller_id=equipment.creator_id,
            quantity=1,
            unit_price=100.0,
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        logger.info(f"Transacción creada: ID {transaction.id}")
        return transaction
    except Exception as e:
        logger.error(f"Error en create_transaction: {str(e)}")
        db.session.rollback()
        raise

def complete_transaction(transaction):
    """Completar transacción y actualizar estado del equipo"""
    try:
        # Obtener el equipo
        equipment = transaction.equipment
        
        # Completar la transacción
        transaction.status = 'Completado'
        transaction.processed_at = datetime.utcnow()
        
        # Procesar la finalización en el equipo
        equipment.process_transaction_completion(transaction)
        
        logger.info(f"Transacción completada: ID {transaction.id}")

    except Exception as e:
        logger.error(f"Error en complete_transaction: {str(e)}")
        db.session.rollback()
        raise

def test_equipment_flow():
    """Probar el flujo completo"""
    with app.app_context():
        try:
            logger.info("Iniciando prueba de flujo de equipos")
            
            # Setup inicial
            admin, seller, buyer, category = setup_test_data()
            logger.info("Datos iniciales configurados correctamente")
            
            # Crear equipo
            equipment = create_test_equipment(seller, category)
            verify_db_state(equipment.id, 'En revisión', 5)
            
            # Publicar equipo
            approve_and_publish_equipment(admin, equipment)
            verify_db_state(equipment.id, 'Publicado', 5)
            
            # Realizar transacciones hasta dejar solo 1 unidad
            for i in range(4):  # Dejamos 1 unidad
                transaction = create_transaction(buyer, equipment)
                complete_transaction(transaction)
                verify_db_state(equipment.id, 'Publicado', 5 - (i + 1))
            
            # Crear la última transacción cuando aún hay 1 unidad
            last_transaction = create_transaction(buyer, equipment)
            verify_db_state(equipment.id, 'Publicado', 1)
            
            # Completar la última transacción (el estado debe cambiar a Agotado)
            complete_transaction(last_transaction)
            equipment = verify_db_state(equipment.id, 'Agotado', 0)
            
            # Intentar crear una nueva transacción (debería fallar)
            try:
                create_transaction(buyer, equipment)
                raise AssertionError("No debería permitir crear una transacción cuando no hay stock")
            except ValueError as e:
                logger.info("Error esperado al intentar crear transacción sin stock: %s", str(e))
            
            # Verificar que el estado sigue siendo Agotado
            equipment = verify_db_state(equipment.id, 'Agotado', 0)
            
            # Rechazar la última transacción y verificar que vuelve a Publicado
            last_transaction.status = 'Rechazado'
            equipment.process_transaction_completion(last_transaction)
            
            # Verificar que el estado vuelve a Publicado con 1 unidad
            equipment = verify_db_state(equipment.id, 'Publicado', 1)

            # Probar marcar manualmente como agotado
            equipment.mark_as_out_of_stock()
            equipment = verify_db_state(equipment.id, 'Agotado', 0)
            
            # Intentar crear una transacción cuando está agotado manualmente
            try:
                create_transaction(buyer, equipment)
                raise AssertionError("No debería permitir crear una transacción cuando está agotado")
            except ValueError as e:
                logger.info("Error esperado al intentar crear transacción con equipo agotado: %s", str(e))

            # Probar actualización manual a 0
            equipment.available_quantity = 0
            equipment.update_status_based_on_quantity()
            db.session.commit()
            equipment = verify_db_state(equipment.id, 'Agotado', 0)

            # Actualizar cantidad manualmente a 1 debería cambiar el estado a Publicado
            equipment.available_quantity = 1
            equipment.update_status_based_on_quantity()
            db.session.commit()
            equipment = verify_db_state(equipment.id, 'Publicado', 1)

        except Exception as e:
            logger.error(f"Error en la prueba: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    test_equipment_flow()
