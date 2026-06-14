from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zenie-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zenie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── DB aur models yahan import karo AFTER app banane ke baad
from models import db, User
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

contacts = []
subscribers = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'buyer')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('signup'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('signup'))

        user = User(name=name, email=email,
                    password=generate_password_hash(password), role=role)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to Zenie, {name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        user     = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=bool(remember))
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    email      = data.get('email', '').strip()
    message    = data.get('message', '').strip()
    if not all([first_name, email, message]):
        return jsonify({'success': False, 'error': 'Name, email, and message required.'}), 400
    contacts.append({'name': first_name, 'email': email, 'message': message})
    return jsonify({'success': True, 'message': "Message received! We'll reply within 2 hours."})

@app.route('/api/newsletter', methods=['POST'])
def newsletter():
    data  = request.get_json()
    email = data.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Valid email required.'}), 400
    if email in subscribers:
        return jsonify({'success': False, 'error': 'Already subscribed!'}), 409
    subscribers.append(email)
    return jsonify({'success': True, 'message': 'Subscribed! Welcome to Zenie 🎉'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)