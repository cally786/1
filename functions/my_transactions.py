from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/my-transactions')
@login_required
def my_transactions():
    # Obtener las transacciones del usuario donde es comprador
    my_reservations = Transaction.query\
        .options(db.joinedload(Transaction.equipment))\
        .options(db.joinedload(Transaction.seller))\
        .filter(Transaction.buyer_id == current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .all()
    
    return render_template('my_transactions.html', transactions=my_reservations)
