from flask_login import login_user, logout_user
from models.user import User
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dont_need_now import get_db


auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Проверка правильности email"""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def validate_password(password):
    """Проверка сложности пароля"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True



auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Проверка правильности email"""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def validate_password(password):
    """Проверка сложности пароля"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Получаем данные из формы
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Проверка корректности email
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('auth.html', title="Register", button_text="Register", toggle_url=url_for('auth.login'), toggle_text="Already have an account? Log In")

        # Проверка сложности пароля
        if not validate_password(password):
            flash('Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.', 'error')
            return render_template('auth.html', title="Register", button_text="Register", toggle_url=url_for('auth.login'), toggle_text="Already have an account? Log In")

        # Проверяем, что пароли совпадают
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth.html', title="Register", button_text="Register", toggle_url=url_for('auth.login'), toggle_text="Already have an account? Log In")

        db = get_db()
        cursor = db.cursor()

        # Проверяем, есть ли уже пользователь с таким email или username
        cursor.execute('SELECT * FROM users WHERE email = %s OR username = %s', (email, username))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email or username already in use', 'error')
            return render_template('auth.html', title="Register", button_text="Register", toggle_url=url_for('auth.login'), toggle_text="Already have an account? Log In")

        # Хэшируем пароль и сохраняем пользователя в базу данных
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
        db.commit()

        # Логиним пользователя сразу после регистрации
        cursor.execute('SELECT id, username, email, password FROM users WHERE email = %s', (email,))
        row = cursor.fetchone()
        user = User(id=row[0], username=row[1], email=row[2], password=row[3])

        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('profile'))

    return render_template('auth.html', title="Register", button_text="Register", toggle_url=url_for('auth.login'), toggle_text="Already have an account? Log In")




@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Проверяем наличие пользователя по email
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, password FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            # Авторизуем пользователя, используя данные из БД
            login_user(User(id=user[0], username=user[1], email=user[2], password=user[3]))
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))

        flash('Invalid email or password', 'error')

    return render_template('auth.html', title="Login", button_text="Log In", toggle_url=url_for('auth.register'), toggle_text="Don\'t have an account? Register")

# Выход из системы
@auth_bp.route('/logout')
def logout():
    logout_user()  # Завершаем сессию пользователя
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))
