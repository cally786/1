# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Asegurarse de que el directorio de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Inicializar extensiones
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Importar modelos
from app.models.models import User, Equipment, Transaction, Notification, Category

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Registrar blueprints
from app.routes.auth_routes import auth as auth_blueprint
from app.routes.main_routes import main as main_blueprint
from app.routes.equipment_routes import equipment as equipment_blueprint
from app.routes.equipment_creation_routes import equipment_creation as equipment_creation_blueprint
from app.routes.transaction_routes import transaction as transaction_blueprint
from app.routes.notification_routes import notification as notification_blueprint
from app.routes.reservation_routes import reservation as reservation_blueprint
from app.routes.transaction_status_routes import transactions_status as transactions_status_blueprint
from app.routes.transaction_approval_routes import transaction_approval as transaction_approval_blueprint
from app.routes.admin_routes import admin as admin_blueprint
from app.routes.published_routes import published as published_blueprint
from app.routes.user_routes import user as user_blueprint
from app.routes.chat_routes import chat as chat_blueprint

app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
app.register_blueprint(equipment_blueprint)
app.register_blueprint(equipment_creation_blueprint)
app.register_blueprint(transaction_blueprint)
app.register_blueprint(notification_blueprint)
app.register_blueprint(reservation_blueprint)
app.register_blueprint(transactions_status_blueprint)
app.register_blueprint(transaction_approval_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(published_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(chat_blueprint, url_prefix='/chats')

def init_db():
    with app.app_context():
        db.create_all()
        
        # Verificar si existe el usuario administrador
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)

        # Crear categorías iniciales
        default_categories = [
            {'name': 'Electrónicos', 'description': 'Equipos electrónicos y dispositivos'},
            {'name': 'Herramientas', 'description': 'Herramientas y equipos de trabajo'},
            {'name': 'Mobiliario', 'description': 'Muebles y equipamiento de oficina'},
            {'name': 'Audiovisual', 'description': 'Equipos de audio y video'},
            {'name': 'Deportivo', 'description': 'Equipamiento deportivo'}
        ]

        for cat_data in default_categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                category = Category(**cat_data)
                db.session.add(category)

        try:
            db.session.commit()
            print("Base de datos inicializada correctamente")
        except Exception as e:
            db.session.rollback()
            print(f"Error al inicializar la base de datos: {str(e)}")
