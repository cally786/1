import re
import os
import shutil
from collections import defaultdict

def clean_previous_organization():
    """Limpiar organización anterior si existe"""
    if os.path.exists('organized_functions'):
        shutil.rmtree('organized_functions')
    print("Limpiando organización anterior...")

def create_directory_structure():
    """Crear la estructura de directorios necesaria"""
    print("Creando estructura de directorios...")
    directories = {
        'auth': ['login', 'users', 'permissions'],
        'equipment': ['management', 'operations', 'details'],
        'transactions': ['operations', 'history'],
        'notifications': ['alerts', 'messages'],
        'utils': ['helpers', 'decorators'],
        'admin': ['management', 'operations'],
        'models': ['user', 'equipment', 'transaction', 'notification']
    }
    
    base_dir = 'organized_functions'
    os.makedirs(base_dir, exist_ok=True)
    
    for main_dir, subdirs in directories.items():
        for subdir in subdirs:
            dir_path = os.path.join(base_dir, main_dir, subdir)
            os.makedirs(dir_path, exist_ok=True)
            print(f"Creado directorio: {dir_path}")

def is_class_method(lines, start_pos):
    """Determinar si una función es un método de clase"""
    # Buscar hacia atrás para encontrar la definición de clase
    current_pos = start_pos
    while current_pos >= 0:
        line = lines[current_pos].strip()
        if line.startswith('class '):
            return True
        if line and not (line.startswith('@') or line.startswith('def ') or not line):
            return False
        current_pos -= 1
    return False

def get_class_name(lines, start_pos):
    """Obtener el nombre de la clase a la que pertenece el método"""
    current_pos = start_pos
    while current_pos >= 0:
        line = lines[current_pos].strip()
        if line.startswith('class '):
            match = re.match(r'class\s+(\w+)', line)
            if match:
                return match.group(1)
        current_pos -= 1
    return None

def extract_function_content(content, start_pos):
    """Extraer el contenido completo de una función"""
    lines = content.split('\n')
    
    # Verificar si es un método de clase
    if is_class_method(lines, start_pos):
        class_name = get_class_name(lines, start_pos)
        if class_name:
            return None, class_name  # No extraer métodos de clase
    
    function_lines = []
    current_pos = start_pos
    
    # Retroceder para encontrar decoradores
    while current_pos > 0 and (
        lines[current_pos - 1].strip().startswith('@') or 
        not lines[current_pos - 1].strip()
    ):
        current_pos -= 1
        function_lines.insert(0, lines[current_pos])
    
    # Obtener la definición de la función y su indentación base
    function_def = lines[start_pos]
    base_indent = len(function_def) - len(function_def.lstrip())
    function_lines.append(function_def)
    
    # Obtener el cuerpo de la función
    current_pos = start_pos + 1
    while current_pos < len(lines):
        line = lines[current_pos]
        if line.strip():  # Si la línea no está vacía
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and not line.strip().startswith('@'):
                break
        function_lines.append(line)
        current_pos += 1
    
    return '\n'.join(function_lines), None

def get_function_category(name, content):
    """Determinar la categoría de una función"""
    name = name.lower()
    content = content.lower()
    
    categories = {
        'auth/login': ['login', 'logout', 'auth'],
        'auth/users': ['user_', 'add_user', 'edit_user', 'delete_user'],
        'equipment/management': ['add_equipment', 'edit_equipment'],
        'equipment/operations': ['delete_equipment', 'reserve_equipment', 'equipment_detail'],
        'transactions/operations': ['transaction', 'reserve', 'cancel'],
        'notifications/alerts': ['notification', 'alert', 'message'],
        'utils/helpers': ['util', 'helper', 'allowed', 'check', 'url_params'],
        'utils/decorators': ['requires_admin', 'login_required'],
        'admin/management': ['admin', 'manage']
    }
    
    # Primero intentar encontrar una coincidencia exacta
    for category, keywords in categories.items():
        if name in keywords:
            return category
    
    # Luego buscar coincidencias parciales
    for category, keywords in categories.items():
        if any(keyword in name for keyword in keywords):
            return category
        if any(keyword in content for keyword in keywords):
            return category
    
    return 'utils/helpers'

def process_functions():
    """Procesar y organizar las funciones"""
    print("Procesando funciones...")
    
    with open('app.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    lines = content.split('\n')
    
    # Encontrar todas las funciones
    function_pattern = r'def\s+(\w+)\s*\('
    functions = list(re.finditer(function_pattern, content))
    
    for match in functions:
        function_name = match.group(1)
        start_line = content.count('\n', 0, match.start())
        
        # Extraer la función completa
        function_content, class_name = extract_function_content(content, start_line)
        
        # Si es un método de clase, guardarlo en la carpeta correspondiente
        if class_name:
            model_type = class_name.lower()
            if model_type in ['user', 'equipment', 'transaction', 'notification']:
                dir_path = f'organized_functions/models/{model_type}'
                file_path = os.path.join(dir_path, f'{function_name}.py')
                
                # Crear el contenido del archivo
                file_content = f"""# Método de la clase {class_name}
from app.models import {class_name}

{function_content}"""
                
                os.makedirs(dir_path, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                print(f"Creado método de clase: {function_name} en models/{model_type}")
                continue
        
        if not function_content:
            continue
        
        # Para funciones normales
        category = get_function_category(function_name, function_content)
        file_path = os.path.join('organized_functions', category, f'{function_name}.py')
        
        # Preparar los imports necesarios
        imports = [
            'from flask import Flask, render_template, request, redirect, url_for, flash, jsonify',
            'from flask_login import login_required, current_user, login_user, logout_user',
            'from app import db',
            'from app.models import User, Equipment, Transaction, Notification',
            'from datetime import datetime',
            'from functools import wraps'
        ]
        
        # Escribir el archivo
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as func_file:
            func_file.write('# Imports necesarios\n')
            func_file.write('\n'.join(imports) + '\n\n')
            func_file.write(function_content)
        
        print(f"Creada función: {function_name} en {category}")

def create_init_files():
    """Crear archivos __init__.py en cada directorio"""
    print("Creando archivos __init__.py...")
    
    for root, dirs, files in os.walk('organized_functions'):
        if files:
            init_path = os.path.join(root, '__init__.py')
            with open(init_path, 'w', encoding='utf-8') as init_file:
                init_file.write('# Archivo generado automáticamente\n\n')
                
                # Importar todas las funciones del directorio
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        module_name = file[:-3]
                        init_file.write(f'from .{module_name} import {module_name}\n')

def main():
    try:
        # Limpiar organización anterior
        clean_previous_organization()
        
        # Crear estructura de directorios
        create_directory_structure()
        
        # Procesar y organizar las funciones
        process_functions()
        
        # Crear archivos __init__.py
        create_init_files()
        
        print("\n¡Organización completada exitosamente!")
        print("Las funciones han sido organizadas en la carpeta 'organized_functions/'")
        
    except Exception as e:
        print(f"Error durante la organización: {str(e)}")

if __name__ == '__main__':
    main()
