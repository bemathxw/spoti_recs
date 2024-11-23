import MySQLdb
from flask import Flask, render_template, g, redirect, url_for, session, flash
from spotify import spotify_bp
from models.user import User
from spotify import get_recommendations, get_top_tracks

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'


# Регистрируем Blueprints
app.register_blueprint(spotify_bp)

# Главная страница
@app.route('/')
def home():
    return render_template('home.html')

# Страница профиля
@app.route('/profile')
def profile():
    """Отображаем профиль пользователя или кнопку входа, если токена нет"""
    # Проверяем наличие токена
    if 'spotify_token' not in session:
        # Если токена нет, рендерим страницу с кнопкой логина
        return render_template('profile.html', show_login_button=True)

    # Если токен есть, показываем рекомендации
    top_tracks = get_top_tracks()

    if not top_tracks:
        flash("Failed to get your top tracks from Spotify.", "error")
        return render_template('profile.html', show_login_button=True)

    # Получаем трек ID для рекомендаций
    track_ids = [track['id'] for track in top_tracks]

    # Получаем рекомендации на основе этих треков
    recommendations = get_recommendations(track_ids)

    # Передаем данные в шаблон
    return render_template('profile.html', top_tracks=top_tracks, recommendations=recommendations,
                           show_login_button=False)


from recommendations import recommendations_bp


app.register_blueprint(recommendations_bp)

# Закрытие соединения с базой данных
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)  # Здесь указываем порт 8080