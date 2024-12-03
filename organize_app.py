import os
import re

def create_directory_structure():
    """Crear la estructura de directorios necesaria"""
    directories = [
        'app',
        'app/routes',
        'app/models',
        'app/utils',
        'app/templates',
        'app/static'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def extract_models():
    """Extraer las clases de modelos"""
    with open('app.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extraer las clases de modelos
    models = []
    model_classes = re.finditer(r'class\s+(\w+)\(.*?db\.Model.*?\):.*?(?=class|\Z)', content, re.DOTALL)
    
    models_content = '''from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

'''
    
    for match in model_classes:
        models.append(match.group(0))
    
    models_content += '\n\n'.join(models)
    
    with open('app/models/models.py', 'w', encoding='utf-8') as file:
        file.write(models_content)

def extract_routes():
    """Extraer las rutas y organizarlas por tipo"""
    with open('app.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Definir categorías de rutas
    route_categories = {
        'auth': {
            'pattern': r'@app\.route\([\'"]\/(?:login|logout|manage-users|add-user|edit-user|delete-user)[\'"].*?\n(?:@[^\n]+\n)*def\s+\w+\([^)]*\):.*?(?=@app\.route|\Z)',
            'imports': '''from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import User
from app.utils.decorators import requires_admin
from app import db

auth_bp = Blueprint('auth', __name__)
'''
        },
        'equipment': {
            'pattern': r'@app\.route\([\'"]\/(?:all-equipment|add-equipment|edit-equipment|delete-equipment|equipment-detail)[\'"].*?\n(?:@[^\n]+\n)*def\s+\w+\([^)]*\):.*?(?=@app\.route|\Z)',
            'imports': '''from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Equipment
from app.utils.decorators import requires_admin
from app import db

equipment_bp = Blueprint('equipment', __name__)
'''
        },
        'transactions': {
            'pattern': r'@app\.route\([\'"]\/(?:transactions|reserve-equipment|cancel-transaction|my-transactions|my-sales)[\'"].*?\n(?:@[^\n]+\n)*def\s+\w+\([^)]*\):.*?(?=@app\.route|\Z)',
            'imports': '''from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Transaction, Equipment, Notification
from app import db

transactions_bp = Blueprint('transactions', __name__)
'''
        }
    }
    
    for category, info in route_categories.items():
        routes = re.finditer(info['pattern'], content, re.DOTALL | re.MULTILINE)
        route_content = info['imports']
        
        for route in routes:
            # Convertir la ruta para usar el blueprint
            route_code = route.group(0).replace('@app.route', '@' + category + '_bp.route')
            route_content += '\n\n' + route_code
        
        with open(f'app/routes/{category}.py', 'w', encoding='utf-8') as file:
            file.write(route_content)

def extract_utils():
    """Extraer funciones de utilidad"""
    with open('app.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    utils_content = '''from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash

'''
    
    # Extraer decoradores y funciones de utilidad
    utils_pattern = r'(?:def\s+requires_admin|def\s+allowed_file|def\s+url_params).*?(?=def|\Z)'
    utils = re.finditer(utils_pattern, content, re.DOTALL)
    
    for util in utils:
        utils_content += util.group(0) + '\n\n'
    
    with open('app/utils/utils.py', 'w', encoding='utf-8') as file:
        file.write(utils_content)

def create_init_file():
    """Crear el archivo __init__.py principal"""
    init_content = '''from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

    # Asegurarse de que el directorio de uploads exista
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.routes.auth import auth_bp
    from app.routes.equipment import equipment_bp
    from app.routes.transactions import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(transactions_bp)

    return app
'''
    
    with open('app/__init__.py', 'w', encoding='utf-8') as file:
        file.write(init_content)

def main():
    # Crear la estructura de directorios
    create_directory_structure()
    
    # Extraer y organizar el código
    extract_models()
    extract_routes()
    extract_utils()
    create_init_file()
    
    print("¡Reorganización completada!")
    print("La nueva estructura ha sido creada en el directorio 'app/'")

if __name__ == '__main__':
    main()
