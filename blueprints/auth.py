"""
Authentication routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    # Validation
    if not username or not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('main.index'))

    if len(username) < 3:
        flash('Username must be at least 3 characters long', 'error')
        return redirect(url_for('main.index'))

    if len(password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('main.index'))

    if '@' not in email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('main.index'))

    # Check if user already exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash('Username or email already exists', 'error')
        return redirect(url_for('main.index'))

    # Create new user
    new_user = User(username=username, email=email, is_admin=False)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Auto-login after registration
    login_user(new_user, remember=True)
    flash(f'Welcome to Opinian, {username}! Your account has been created.', 'success')

    return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))

