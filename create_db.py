from app import app, db
from app.models.models import User, Equipment, Transaction, Notification

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    print("Database created successfully!")
