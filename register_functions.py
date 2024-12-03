import os
import re

def get_import_statement(file_path):
    """Genera la declaración de importación basada en la ruta del archivo"""
    # Convertir la ruta del archivo a un módulo Python
    module_path = file_path.replace('organized_functions/', '').replace('.py', '').replace('/', '.')
    function_name = os.path.basename(file_path)[:-3]  # Eliminar .py
    return f"from organized_functions.{module_path} import {function_name}"

def get_blueprint_registration(function_name, file_path):
    """Genera el código para registrar la función en el blueprint correspondiente"""
    # Determinar el blueprint basado en la ruta del archivo
    if 'auth' in file_path:
        return f"auth_bp.add_url_rule('/{function_name}', '{function_name}', {function_name}, methods=['GET', 'POST'])"
    elif 'equipment' in file_path:
        return f"equipment_bp.add_url_rule('/{function_name}', '{function_name}', {function_name}, methods=['GET', 'POST'])"
    elif 'transactions' in file_path:
        return f"transactions_bp.add_url_rule('/{function_name}', '{function_name}', {function_name}, methods=['GET', 'POST'])"
    elif 'admin' in file_path:
        return f"admin_bp.add_url_rule('/{function_name}', '{function_name}', {function_name}, methods=['GET', 'POST'])"
    else:
        return f"app.add_url_rule('/{function_name}', '{function_name}', {function_name}, methods=['GET', 'POST'])"

def main():
    # Leer el contenido actual de app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Preparar las nuevas importaciones y registros
    imports = []
    registrations = []

    # Recorrer todos los archivos .py en organized_functions
    for root, _, files in os.walk('organized_functions'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file).replace('\\', '/')
                if 'models' not in file_path:  # Ignorar los archivos en la carpeta models
                    function_name = file[:-3]
                    imports.append(get_import_statement(file_path))
                    registrations.append(get_blueprint_registration(function_name, file_path))

    # Encontrar la posición donde insertar las importaciones
    import_pos = content.find('# Importaciones de funciones')
    if import_pos == -1:
        import_pos = content.find('from flask import')
        if import_pos == -1:
            print("No se pudo encontrar un lugar adecuado para las importaciones")
            return

    # Encontrar la posición donde insertar los registros de blueprint
    register_pos = content.find('# Registro de rutas')
    if register_pos == -1:
        register_pos = content.find('if __name__ ==')
        if register_pos == -1:
            print("No se pudo encontrar un lugar adecuado para los registros")
            return

    # Crear el nuevo contenido
    new_content = (
        content[:import_pos] + 
        "# Importaciones de funciones\n" + 
        "\n".join(imports) + "\n\n" +
        content[import_pos:register_pos] +
        "# Registro de rutas\n" +
        "\n".join(registrations) + "\n\n" +
        content[register_pos:]
    )

    # Hacer backup del archivo original
    os.rename('app.py', 'app.py.bak')

    # Escribir el nuevo contenido
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Se ha actualizado app.py exitosamente!")
    print("Se ha creado una copia de respaldo en app.py.bak")

if __name__ == '__main__':
    main()
