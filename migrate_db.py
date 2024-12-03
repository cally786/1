from app import app, db
from datetime import datetime
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        # Agregar la columna published_at
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE equipment ADD COLUMN published_at DATETIME'))
            
            # Actualizar la fecha de publicación para equipos ya publicados
            conn.execute(text('''
                UPDATE equipment 
                SET published_at = created_at 
                WHERE status = 'Publicado'
            '''))
            
            conn.commit()
        
        print("Migración completada exitosamente.")

if __name__ == '__main__':
    migrate_database()
