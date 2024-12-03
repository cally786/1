from app import app, db
from sqlalchemy import text

with app.app_context():
    # Verificar si la columna ya existe
    with db.engine.connect() as conn:
        result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM pragma_table_info('notification')
        WHERE name='equipment_id'
        """)).scalar()
        
        if result == 0:
            # La columna no existe, agregarla
            conn.execute(text("""
            ALTER TABLE notification 
            ADD COLUMN equipment_id INTEGER
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY
            )
            """))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notification (
                equipment_id INTEGER,
                FOREIGN KEY (equipment_id) REFERENCES equipment (id)
            )
            """))
            conn.commit()
            print("Columna equipment_id agregada exitosamente")
