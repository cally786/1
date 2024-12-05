# models/models.py

from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy import inspect

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    notifications = db.relationship('Notification', backref='recipient', lazy=True,
                                    foreign_keys='Notification.recipient_id')
    equipment_items = db.relationship('Equipment', back_populates='creator')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con Equipment
    equipment = db.relationship('Equipment', back_populates='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), unique=True)
    unit_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    status = db.Column(db.String(20), default='En revisión')  # En revisión, Publicado, Agotado, Vendido
    location = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer)
    image_filename = db.Column(db.String(255))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    category = db.relationship('Category', back_populates='equipment')
    creator = db.relationship('User', back_populates='equipment_items')
    transactions = db.relationship('Transaction', back_populates='equipment')
    equipment_notifications = db.relationship('Notification', back_populates='equipment')

    def __init__(self, **kwargs):
        super(Equipment, self).__init__(**kwargs)
        if self.available_quantity is None:
            self.available_quantity = self.quantity

    def __repr__(self):
        return f'<Equipment {self.name}>'

    def mark_as_out_of_stock(self):
        """Marca el equipo como agotado manualmente"""
        if self.status not in ['En revisión', 'Rechazado']:
            self.status = 'Agotado'
            self.available_quantity = 0
            db.session.commit()
            return True
        return False

    def update_status_based_on_quantity(self):
        """Actualiza el estado del equipo basado en la cantidad disponible"""
        if self.status not in ['En revisión', 'Rechazado']:
            if self.available_quantity == 0:
                self.status = 'Agotado'
                # Notificar al vendedor
                notification = Notification(
                    recipient_id=self.creator_id,
                    message=f'Tu producto "{self.name}" se ha marcado como agotado.',
                    type='stock_empty'
                )
                db.session.add(notification)
            elif self.available_quantity > 0 and self.status == 'Agotado':
                self.status = 'Publicado'
                # Notificar al vendedor
                notification = Notification(
                    recipient_id=self.creator_id,
                    message=f'Tu producto "{self.name}" está nuevamente disponible con {self.available_quantity} unidades.',
                    type='stock_available'
                )
                db.session.add(notification)

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'before_update')
        def receive_before_update(mapper, connection, target):
            state = inspect(target)
            if state.attrs.available_quantity.history.has_changes():
                target.update_status_based_on_quantity()

    def process_transaction_completion(self, transaction):
        """Procesa la finalización de una transacción"""
        if transaction.status == 'Completado':
            # Confirmar la reducción de cantidad
            self.available_quantity = max(0, self.available_quantity - transaction.quantity)
            self.update_status_based_on_quantity()
        elif transaction.status == 'Rechazado':
            # Devolver la cantidad reservada
            self.available_quantity += transaction.quantity
            self.update_status_based_on_quantity()
        
        db.session.commit()

    def check_quantity_status(self, requested_quantity):
        """
        Verifica si hay suficiente cantidad disponible para una reserva.
        
        Args:
            requested_quantity (int): Cantidad solicitada para la reserva
            
        Returns:
            tuple: (bool, str) - (True si hay suficiente cantidad, mensaje de estado)
        """
        if requested_quantity <= 0:
            return False, "La cantidad solicitada debe ser mayor a 0"
            
        if self.available_quantity is None:
            self.available_quantity = self.quantity
            
        if requested_quantity > self.available_quantity:
            return False, f"No hay suficiente cantidad disponible. Cantidad disponible: {self.available_quantity}"
            
        if self.status != 'Publicado':
            return False, "Este equipo no está disponible para reserva"
            
        return True, "Cantidad disponible"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pendiente')
    processed_at = db.Column(db.DateTime)
    
    # Relaciones
    equipment = db.relationship('Equipment', back_populates='transactions')
    buyer = db.relationship('User', foreign_keys=[buyer_id])
    seller = db.relationship('User', foreign_keys=[seller_id])
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)
    
    # Relaciones
    equipment = db.relationship('Equipment', back_populates='equipment_notifications')

    def get_icon(self):
        icons = {
            'new_reservation': 'shopping-cart',
            'transaction_approved': 'check-circle',
            'transaction_rejected': 'times-circle',
            'out_of_stock': 'exclamation-triangle',
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'success': 'check-circle',
            'error': 'times-circle',
            'stock_empty': 'exclamation-triangle',
            'stock_available': 'check-circle'
        }
        return icons.get(self.type, 'bell')

    def get_color(self):
        colors = {
            'new_reservation': 'text-primary',
            'transaction_approved': 'text-success',
            'transaction_rejected': 'text-danger',
            'out_of_stock': 'text-warning',
            'info': 'text-info',
            'warning': 'text-warning',
            'success': 'text-success',
            'error': 'text-danger',
            'stock_empty': 'text-warning',
            'stock_available': 'text-success'
        }
        return colors.get(self.type, 'text-info')
