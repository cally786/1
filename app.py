from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'  # Base de datos persistente
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Asegurarse de que el directorio de uploads exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar la base de datos
db = SQLAlchemy(app)

# Configurar el sistema de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Importar modelos
from models.models import User, Equipment, Transaction, Notification

# Importar funciones auxiliares
from utils.helpers import requires_admin, allowed_file, url_params

# Importar rutas
from app.routes.auth_routes import auth
from app.routes.main_routes import main
from app.routes.equipment_routes import equipment
from app.routes.user_routes import user
from app.routes.transaction_routes import transaction
from app.routes.notification_routes import notification

# Registrar blueprints
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(equipment)
app.register_blueprint(user)
app.register_blueprint(transaction)
app.register_blueprint(notification)

def init_db():
    """Initialize the database."""
    with app.app_context():
        # Crear todas las tablas si no existen
        db.create_all()
        
        # Crear usuario admin por defecto si no existe
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                is_admin=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()

if __name__ == '__main__':
    init_db()  # Inicializar la base de datos al iniciar la aplicación
    app.run(debug=True)
