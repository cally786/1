from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app, db

migrate = Migrate(app, db)

if __name__ == '__main__':
    # No necesitamos crear las tablas manualmente
    # Flask-Migrate se encargará de eso
    pass
