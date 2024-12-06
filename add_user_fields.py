from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Configuración de la aplicación
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db = SQLAlchemy(app)

def upgrade():
    with app.app_context():
        # Agregar las nuevas columnas
        with db.engine.connect() as conn:
            try:
                conn.execute('ALTER TABLE user ADD COLUMN first_name VARCHAR(50)')
                print("Agregada columna first_name")
            except Exception as e:
                print(f"Error o columna first_name ya existe: {str(e)}")
            
            try:
                conn.execute('ALTER TABLE user ADD COLUMN last_name VARCHAR(50)')
                print("Agregada columna last_name")
            except Exception as e:
                print(f"Error o columna last_name ya existe: {str(e)}")
            
            try:
                conn.execute('ALTER TABLE user ADD COLUMN company VARCHAR(100)')
                print("Agregada columna company")
            except Exception as e:
                print(f"Error o columna company ya existe: {str(e)}")
            
            try:
                conn.execute('ALTER TABLE user ADD COLUMN phone VARCHAR(20)')
                print("Agregada columna phone")
            except Exception as e:
                print(f"Error o columna phone ya existe: {str(e)}")
            
if __name__ == '__main__':
    upgrade()
