# Sistema de Inventario para Telecomunicaciones

Esta es una aplicación web desarrollada con Flask para gestionar el inventario de equipos de telecomunicaciones.

## Características

- Registro de equipos con información detallada
- Seguimiento del estado de los equipos (En stock, Instalado, En mantenimiento)
- Gestión de ubicaciones
- Interfaz de usuario intuitiva y responsive
- Sistema de notificaciones para operaciones CRUD

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio o descargar los archivos

2. Crear un entorno virtual (recomendado):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Activar el entorno virtual (si no está activado):
```bash
venv\Scripts\activate
```

2. Ejecutar la aplicación:
```bash
python app.py
```

3. Abrir un navegador web y visitar:
```
http://localhost:5000
```

## Estructura del Proyecto

```
App inventario/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias del proyecto
├── templates/         # Plantillas HTML
│   ├── base.html     # Plantilla base
│   ├── index.html    # Página principal
│   ├── add_equipment.html    # Formulario para agregar equipo
│   └── edit_equipment.html   # Formulario para editar equipo
└── README.md          # Este archivo
```

## Contribuir

Si deseas contribuir al proyecto:

1. Haz un Fork del repositorio
2. Crea una nueva rama para tus cambios
3. Realiza tus cambios y haz commit
4. Envía un pull request

## Licencia

Este proyecto está bajo la Licencia MIT.
