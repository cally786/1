import ast
import os
import shutil

# Nombre del archivo original
ORIGINAL_FILE = 'app.py'

# Directorio base
BASE_DIR = '.'

# Directorios para los módulos
MODELS_DIR = os.path.join(BASE_DIR, 'models')
ROUTES_DIR = os.path.join(BASE_DIR, 'routes')
UTILS_DIR = os.path.join(BASE_DIR, 'utils')

# Crear la estructura de directorios
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ROUTES_DIR, exist_ok=True)
os.makedirs(UTILS_DIR, exist_ok=True)

# Leer el código original
with open(ORIGINAL_FILE, 'r', encoding='utf-8') as f:
    code = f.read()

# Analizar el código AST
tree = ast.parse(code)

# Separar las definiciones
imports = []
classes = []
functions = []
others = []

for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        imports.append(node)
    elif isinstance(node, ast.ClassDef):
        classes.append(node)
    elif isinstance(node, ast.FunctionDef):
        functions.append(node)
    else:
        others.append(node)

# Función para convertir nodos AST a código fuente
def nodes_to_code(nodes):
    return '\n\n'.join([ast.unparse(node) for node in nodes])

# Separar las clases en modelos y otras clases
models = []
other_classes = []

for cls in classes:
    base_names = []
    for base in cls.bases:
        if isinstance(base, ast.Name):
            base_names.append(base.id)
        elif isinstance(base, ast.Attribute):
            base_names.append(base.attr)
        elif isinstance(base, ast.Call):
            if isinstance(base.func, ast.Name):
                base_names.append(base.func.id)
            elif isinstance(base.func, ast.Attribute):
                base_names.append(base.func.attr)
    if 'db.Model' in base_names or 'UserMixin' in base_names:
        models.append(cls)
    else:
        other_classes.append(cls)

# Separar funciones en rutas, decoradores y utilidades
routes = []
decorators = []
utils = []

for func in functions:
    decorator_names = []
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Name):
            decorator_names.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            decorator_names.append(decorator.attr)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                decorator_names.append(decorator.func.id)
            elif isinstance(decorator.func, ast.Attribute):
                decorator_names.append(decorator.func.attr)
    if 'route' in decorator_names:
        routes.append(func)
    elif any(decorator in ['wraps', 'user_loader', 'context_processor'] for decorator in decorator_names):
        decorators.append(func)
    else:
        utils.append(func)

# Crear models.py
with open(os.path.join(MODELS_DIR, 'models.py'), 'w', encoding='utf-8') as f:
    f.write("from .. import db\n")
    f.write("from flask_login import UserMixin\n")
    f.write("from datetime import datetime\n")
    f.write("from werkzeug.security import generate_password_hash, check_password_hash\n\n")
    f.write(nodes_to_code(models))

# Crear utils.py
with open(os.path.join(UTILS_DIR, 'utils.py'), 'w', encoding='utf-8') as f:
    f.write("from functools import wraps\n")
    f.write("from flask import request, url_for, flash, redirect\n")
    f.write("from flask_login import current_user\n")
    f.write("import os\n\n")
    f.write(nodes_to_code(decorators + utils))

# Crear routes.py
with open(os.path.join(ROUTES_DIR, 'routes.py'), 'w', encoding='utf-8') as f:
    f.write("from flask import render_template, request, redirect, url_for, flash, jsonify, abort\n")
    f.write("from flask_login import login_user, login_required, logout_user, current_user\n")
    f.write("from werkzeug.utils import secure_filename\n")
    f.write("from datetime import datetime\n")
    f.write("import os\n\n")
    f.write("from .. import app, db\n")
    f.write("from ..models.models import *\n")
    f.write("from ..utils.utils import *\n\n")
    f.write(nodes_to_code(routes))

# Crear __init__.py en cada paquete
open(os.path.join(MODELS_DIR, '__init__.py'), 'w').close()
open(os.path.join(ROUTES_DIR, '__init__.py'), 'w').close()
open(os.path.join(UTILS_DIR, '__init__.py'), 'w').close()

# Modificar app.py
with open(ORIGINAL_FILE, 'w', encoding='utf-8') as f:
    # Escribir las importaciones iniciales
    f.write("from flask import Flask\n")
    f.write("from flask_sqlalchemy import SQLAlchemy\n")
    f.write("from flask_login import LoginManager\n")
    f.write("import os\n\n")
    f.write("# Configuración de la aplicación\n")
    f.write("app = Flask(__name__)\n")
    f.write("app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'\n")
    f.write("app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'\n")
    f.write("app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False\n")
    f.write("app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')\n")
    f.write("app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024\n\n")
    f.write("# Asegurarse de que el directorio de uploads exista\n")
    f.write("os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)\n\n")
    f.write("# Inicializar extensiones\n")
    f.write("db = SQLAlchemy(app)\n")
    f.write("login_manager = LoginManager()\n")
    f.write("login_manager.init_app(app)\n")
    f.write("login_manager.login_view = 'login'\n\n")
    f.write("# Importar módulos\n")
    f.write("from models.models import *\n")
    f.write("from routes.routes import *\n")
    f.write("from utils.utils import *\n\n")
    # Agregar el código restante
    if others:
        f.write(nodes_to_code(others))

print("Código reorganizado exitosamente. Las funciones y clases han sido extraídas y el archivo app.py ha sido modificado.")
