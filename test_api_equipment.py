import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
from werkzeug.security import generate_password_hash

BASE_URL = "http://localhost:5000"

def print_response_info(response):
    print(f"\n=== {response.url} ===")
    print(f"Status Code: {response.status_code}")
    print(f"Cookies: {dict(response.cookies)}")
    if 'text/html' in response.headers.get('content-type', ''):
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "No title found"
        print(f"Page Title: {title}")
        
        # Buscar mensajes flash
        flash_messages = soup.find_all(class_=['alert', 'flash'])
        if flash_messages:
            print("\nMensajes del sistema:")
            for msg in flash_messages:
                print(f"- {msg.get_text().strip()}")
    print("=" * 50)

def get_equipment_from_db(equipment_id):
    """Obtiene información del equipo desde la base de datos"""
    conn = sqlite3.connect('instance/inventory.db')
    cursor = conn.cursor()
    
    print("\n=== Estructura de la base de datos ===\n")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute('PRAGMA table_info("{}")'.format(table_name))
            columns = cursor.fetchall()
            print(f"Tabla: {table_name}")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            print()
        except sqlite3.Error as e:
            print(f"Error al obtener información de la tabla {table_name}: {e}")
    
    try:
        # Obtener información del equipo
        cursor.execute("""
            SELECT e.*, 
                   (SELECT COUNT(*) FROM "transaction" t 
                    WHERE t.equipment_id = e.id AND t.status = 'Pendiente') as pending_transactions
            FROM equipment e
            WHERE e.id = ?
        """, (equipment_id,))
        equipment = cursor.fetchone()
        
        if equipment:
            # Obtener las columnas
            columns = [description[0] for description in cursor.description]
            equipment_dict = dict(zip(columns, equipment))
            
            # Obtener transacciones relacionadas
            cursor.execute("""
                SELECT id, status, buyer_id as user_id, created_at, quantity
                FROM "transaction"
                WHERE equipment_id = ?
                ORDER BY created_at DESC
            """, (equipment_id,))
            transactions = cursor.fetchall()
            
            if transactions:
                transaction_columns = ['id', 'status', 'user_id', 'created_at', 'quantity']
                equipment_dict['transactions'] = [
                    dict(zip(transaction_columns, t)) for t in transactions
                ]
            else:
                equipment_dict['transactions'] = []
                
            return equipment_dict
    except sqlite3.Error as e:
        print(f"Error al consultar la base de datos: {e}")
    finally:
        conn.close()
    return None

def update_equipment_status(equipment_id, new_status):
    """Actualiza el estado de un equipo en la base de datos"""
    conn = sqlite3.connect('instance/inventory.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE equipment 
            SET status = ? 
            WHERE id = ?
        """, (new_status, equipment_id))
        conn.commit()
        print(f"\nEstado del equipo {equipment_id} actualizado a: {new_status}")
    except sqlite3.Error as e:
        print(f"Error al actualizar el estado: {e}")
    finally:
        conn.close()

def create_test_user(session):
    """Crea un usuario normal de prueba"""
    timestamp = int(time.time())
    username = f"test_user_{timestamp}"
    email = f"{username}@example.com"
    password = "password123"

    # Crear usuario en la base de datos
    conn = sqlite3.connect('instance/database.db')
    try:
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO user (email, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (email, hashed_password, False))
        user_id = cursor.lastrowid
        conn.commit()
        print("\nUsuario creado exitosamente:")
        print(f"ID: {user_id}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        return email, password
    finally:
        conn.close()

def login_user(session, email, password):
    """Inicia sesión con el usuario especificado"""
    print(f"\nIniciando sesión como {email}")
    
    # Prepare login data
    login_data = {
        'email': email,
        'password': password
    }
    
    # Attempt login
    print("\n=== Intento de login ===")
    response = session.post(
        f"{BASE_URL}/auth/login",
        data=login_data,
        allow_redirects=False  # No seguir redirecciones para ver el resultado real
    )
    print_response_info(response)
    
    # Si el login es exitoso, la respuesta será una redirección a '/'
    if response.status_code == 302:
        session.cookies.update(response.cookies)
        return response.cookies.get('session')
    return None

def logout_user(session):
    """Cierra la sesión actual"""
    print("\nCerrando sesión...")
    response = session.get(f"{BASE_URL}/auth/logout")
    print_response_info(response)
    session.cookies.clear()  # Limpiar todas las cookies de la sesión
    return response

def reserve_equipment(session, equipment_id):
    """Reserva un equipo"""
    print("\nIntentando reservar el equipo como usuario normal...")
    print("\n=== Intento de reserva ===")
    
    # Datos de la reserva
    reserve_data = {
        'quantity': 1,  # Cantidad a reservar
        'equipment_id': equipment_id
    }
    
    response = session.post(
        f"{BASE_URL}/transaction/equipment/{equipment_id}/reserve",
        data=reserve_data,
        allow_redirects=True
    )
    print_response_info(response)
    
    return response

def test_equipment_flow():
    # Create a session that will maintain cookies
    session = requests.Session()
    
    # Login as admin
    print("\nIniciando sesión como admin@example.com")
    session_cookie = login_user(session, "admin@example.com", "admin123")
    
    if not session_cookie:
        print("Error: No se pudo iniciar sesión como admin")
        return
    
    # 2. Crear nuevo equipo con número de serie único
    print("\nIntentando crear nuevo equipo de prueba...")
    serial_number = f"TEST{int(time.time())}"  # Número de serie único
    equipment_data = {
        "name": "Equipo Test Requests",
        "description": "Equipo para pruebas con requests",
        "quantity": "5",
        "category_id": "1",
        "location": "Almacén A",
        "company": "Test Company",
        "model": "Test Model",
        "serial_number": serial_number,
        "unit_price": "100.00",
        "notes": "Notas de prueba",
        "status": "En revisión"
    }
    response = session.post(f"{BASE_URL}/add_equipment", 
                          data=equipment_data,
                          headers={'Referer': f"{BASE_URL}/add_equipment"},
                          allow_redirects=True)
    print_response_info(response)
    
    # 3. Verificar estado inicial del equipo en la DB
    equipment_id = 1  # Asumimos que existe
    print(f"\nVerificando estado del equipo ID {equipment_id} en la base de datos...")
    equipment_info = get_equipment_from_db(equipment_id)
    
    if equipment_info:
        print("\n=== Estado inicial del Equipo en DB ===")
        print(f"ID: {equipment_info['id']}")
        print(f"Nombre: {equipment_info['name']}")
        print(f"Descripción: {equipment_info['description']}")
        print(f"Estado: {equipment_info['status']}")
        print(f"Cantidad: {equipment_info['quantity']}")
        print(f"Cantidad Disponible: {equipment_info['available_quantity']}")
        print(f"Ubicación: {equipment_info['location']}")
        print(f"Compañía: {equipment_info['company']}")
        print(f"Modelo: {equipment_info['model']}")
        print(f"Número de Serie: {equipment_info['serial_number']}")
        print(f"Precio Unitario: {equipment_info['unit_price']}")
        print(f"ID Creador: {equipment_info['creator_id']}")
        print(f"ID Categoría: {equipment_info['category_id']}")
        print(f"Fecha Creación: {equipment_info['created_at']}")
        
        # Actualizar estado a Publicado si no lo está
        if equipment_info['status'] != 'Publicado':
            print("\nActualizando estado del equipo a Publicado...")
            update_equipment_status(equipment_id, 'Publicado')
            equipment_info = get_equipment_from_db(equipment_id)
            print("\n=== Estado del Equipo después de actualización ===")
            print(f"ID: {equipment_info['id']}")
            print(f"Nombre: {equipment_info['name']}")
            print(f"Estado: {equipment_info['status']}")
            print(f"Cantidad Disponible: {equipment_info['available_quantity']}")
    
    # 4. Crear usuario normal para pruebas
    print("\nCreando usuario normal para pruebas...")
    test_user_email, test_user_password = create_test_user(session)
    
    if not test_user_email:
        print("Error: No se pudo crear el usuario de prueba")
        return
    
    # 5. Logout del admin
    logout_user(session)
    
    # 6. Login como usuario normal recién creado
    print("\nIniciando sesión como", test_user_email)
    session_cookie = login_user(session, test_user_email, "password123")
    
    # 7. Verificar estado antes de reservar
    print("\nVerificando estado antes de la reserva...")
    equipment_info = get_equipment_from_db(equipment_id)
    if equipment_info:
        print("\n=== Estado del Equipo antes de reserva ===")
        print(f"ID: {equipment_info['id']}")
        print(f"Nombre: {equipment_info['name']}")
        print(f"Estado: {equipment_info['status']}")
        print(f"Cantidad Disponible: {equipment_info['available_quantity']}")
        if equipment_info['transactions']:
            print("\nTransacciones existentes:")
            for trans in equipment_info['transactions']:
                print(f"  - ID: {trans['id']}")
                print(f"    Estado: {trans['status']}")
                print(f"    Usuario ID: {trans['user_id']}")
                print(f"    Fecha: {trans['created_at']}")
                print(f"    Cantidad: {trans['quantity']}")
    
    # 8. Intentar reservar el equipo
    reserve_response = reserve_equipment(session, equipment_id)
    
    # 9. Verificar estado inmediatamente después de la reserva
    print("\nVerificando estado después de la reserva...")
    equipment_info = get_equipment_from_db(equipment_id)
    if equipment_info:
        print("\n=== Estado del Equipo después de reserva ===")
        print(f"ID: {equipment_info['id']}")
        print(f"Nombre: {equipment_info['name']}")
        print(f"Estado: {equipment_info['status']}")
        print(f"Cantidad Disponible: {equipment_info['available_quantity']}")
        if equipment_info['transactions']:
            print("\nTransacciones después de reserva:")
            for trans in equipment_info['transactions']:
                print(f"  - ID: {trans['id']}")
                print(f"    Estado: {trans['status']}")
                print(f"    Usuario ID: {trans['user_id']}")
                print(f"    Fecha: {trans['created_at']}")
                print(f"    Cantidad: {trans['quantity']}")
    
    # 10. Logout del usuario normal
    logout_user(session)
    
    # 11. Login como admin para revisar y aprobar la reserva
    print("\nIniciando sesión como admin@example.com")
    session_cookie = login_user(session, "admin@example.com", "admin123")
    
    # 12. Obtener y mostrar las transacciones pendientes
    print("\nVerificando transacciones pendientes como admin...")
    response = session.get(f"{BASE_URL}/transactions")
    print_response_info(response)
    
    # 13. Verificar estado final
    print("\nVerificando estado final del equipo...")
    equipment_info = get_equipment_from_db(equipment_id)
    if equipment_info:
        print("\n=== Estado Final del Equipo ===")
        print(f"ID: {equipment_info['id']}")
        print(f"Nombre: {equipment_info['name']}")
        print(f"Estado: {equipment_info['status']}")
        print(f"Cantidad Disponible: {equipment_info['available_quantity']}")
        if equipment_info['transactions']:
            print("\nTransacciones finales:")
            for trans in equipment_info['transactions']:
                print(f"  - ID: {trans['id']}")
                print(f"    Estado: {trans['status']}")
                print(f"    Usuario ID: {trans['user_id']}")
                print(f"    Fecha: {trans['created_at']}")
                print(f"    Cantidad: {trans['quantity']}")

if __name__ == "__main__":
    test_equipment_flow()
