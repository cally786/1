from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from app.models import User, Equipment, Transaction, Notification
from app import db


@app.route('/transactions')
@login_required
def transactions():
    if current_user.is_admin:
        all_transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
        return render_template('transactions.html', all_transactions=all_transactions)
    else:
        purchases = Transaction.query.filter_by(buyer_id=current_user.id)\
            .order_by(Transaction.created_at.desc()).all()
        sales = Transaction.query.filter_by(seller_id=current_user.id)\
            .order_by(Transaction.created_at.desc()).all()
        return render_template('transactions.html', purchases=purchases, sales=sales)
