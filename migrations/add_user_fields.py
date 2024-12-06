from app import app, db
from app.models.models import User

def upgrade():
    with app.app_context():
        # Agregar las nuevas columnas
        with db.engine.connect() as conn:
            conn.execute('ALTER TABLE user ADD COLUMN first_name VARCHAR(50)')
            conn.execute('ALTER TABLE user ADD COLUMN last_name VARCHAR(50)')
            conn.execute('ALTER TABLE user ADD COLUMN company VARCHAR(100)')
            conn.execute('ALTER TABLE user ADD COLUMN phone VARCHAR(20)')
            
if __name__ == '__main__':
    upgrade()
