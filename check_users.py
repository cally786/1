from app import app, db
from app.models.models import User

with app.app_context():
    users = User.query.all()
    print('\nUsuarios en la base de datos:')
    for user in users:
        print(f'ID: {user.id}, Email: {user.email}, Admin: {user.is_admin}')
