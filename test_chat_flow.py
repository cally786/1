from app import app, db
from app.models.models import User
from app.models.chat import Chat, ChatMessage
from datetime import datetime
import time

def test_chat_flow():
    with app.app_context():
        print("\n1. Configurando usuarios de prueba...")
        # Crear usuario admin si no existe
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = User(email='admin@test.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Crear usuario normal si no existe
        user = User.query.filter_by(email='user@test.com').first()
        if not user:
            user = User(email='user@test.com', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
        
        db.session.commit()
        
        print("\n2. Creando nuevo chat...")
        # Usuario crea un nuevo chat
        chat = Chat(
            title="Consulta sobre equipo",
            user_id=user.id,
            status='Pendiente'
        )
        db.session.add(chat)
        db.session.commit()
        print(f"Chat creado con ID: {chat.id}")
        print(f"Estado inicial: {chat.status}")
        
        print("\n3. Usuario envía primer mensaje...")
        # Usuario envía el primer mensaje
        message1 = ChatMessage(
            chat_id=chat.id,
            sender_id=user.id,
            content="Hola, tengo una consulta sobre un equipo"
        )
        db.session.add(message1)
        db.session.commit()
        print(f"Mensaje enviado: {message1.content}")
        
        print("\n4. Admin acepta el chat...")
        # Admin acepta el chat
        chat.assign_admin(admin.id)
        print(f"Estado después de aceptar: {chat.status}")
        print(f"Admin asignado: {chat.admin.email}")
        
        print("\n5. Admin responde con tres mensajes...")
        # Admin envía tres mensajes
        admin_messages = [
            "¡Hola! ¿En qué puedo ayudarte?",
            "Estoy aquí para resolver tus dudas sobre el equipo",
            "¿Podrías darme más detalles sobre tu consulta?"
        ]
        
        for content in admin_messages:
            message = ChatMessage(
                chat_id=chat.id,
                sender_id=admin.id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            print(f"Admin envió: {content}")
            time.sleep(1)  # Simular delay entre mensajes
        
        print("\n6. Usuario responde con tres mensajes...")
        # Usuario envía tres mensajes
        user_messages = [
            "Gracias por responder",
            "Me interesa saber sobre el precio del equipo X",
            "Y también sobre su disponibilidad"
        ]
        
        for content in user_messages:
            message = ChatMessage(
                chat_id=chat.id,
                sender_id=user.id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            print(f"Usuario envió: {content}")
            time.sleep(1)  # Simular delay entre mensajes
        
        print("\n7. Intercambio de mensajes uno a uno...")
        # Intercambio uno a uno
        exchanges = [
            (admin.id, "El equipo X tiene un precio de $1000"),
            (user.id, "¿Ese precio incluye el envío?"),
            (admin.id, "Sí, el envío está incluido dentro de la ciudad"),
            (user.id, "Perfecto, me interesa comprarlo")
        ]
        
        for sender_id, content in exchanges:
            message = ChatMessage(
                chat_id=chat.id,
                sender_id=sender_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            sender_type = "Admin" if sender_id == admin.id else "Usuario"
            print(f"{sender_type} envió: {content}")
            time.sleep(1)  # Simular delay entre mensajes
        
        print("\n8. Verificando mensajes no leídos...")
        # Verificar mensajes no leídos para el admin
        unread_admin = ChatMessage.query.filter_by(
            chat_id=chat.id,
            is_read=False,
            sender_id=user.id
        ).count()
        print(f"Mensajes no leídos para admin: {unread_admin}")
        
        # Verificar mensajes no leídos para el usuario
        unread_user = ChatMessage.query.filter_by(
            chat_id=chat.id,
            is_read=False,
            sender_id=admin.id
        ).count()
        print(f"Mensajes no leídos para usuario: {unread_user}")
        
        print("\n9. Cerrando el chat...")
        # Admin cierra el chat
        chat.close()
        print(f"Estado final del chat: {chat.status}")
        print(f"Chat cerrado en: {chat.closed_at}")

if __name__ == '__main__':
    test_chat_flow()
