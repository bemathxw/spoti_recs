import re
import requests
from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from spotify import get_headers

recommendations_bp = Blueprint('recommendations', __name__)

# Функция для извлечения ID из Spotify ссылок
def extract_spotify_id(link, item_type):
    pattern = rf'https://open\.spotify\.com/{item_type}/([a-zA-Z0-9]+)'
    match = re.search(pattern, link)
    if match:
        return match.group(1)
    return None

@recommendations_bp.route('/customize-recommendations', methods=['GET', 'POST'])
def customize_recommendations():
    """Страница с ползунками для настройки рекомендаций"""
    headers = get_headers()

    if 'spotify_token' not in session:
        flash('Please log in with Spotify.', 'error')
        return redirect(url_for('spotify.login_spotify'))

    if request.method == 'POST':

        track_link = request.form.get('track_link')
        artist_link = request.form.get('artist_link')

        track_id = extract_spotify_id(track_link, 'track')
        artist_id = extract_spotify_id(artist_link, 'artist') if artist_link else None

        if not track_id:
            flash('Invalid track link.', 'error')
            return redirect(url_for('recommendations.customize_recommendations'))

        if not artist_id:
            track_details_url = f"https://api.spotify.com/v1/tracks/{track_id}"
            track_response = requests.get(track_details_url, headers=headers)
            if track_response.status_code == 200:
                artist_id = track_response.json()['artists'][0]['id']
            else:
                flash('Failed to retrieve artist from track.', 'error')
                return redirect(url_for('recommendations.customize_recommendations'))

        params = {
            'seed_tracks': track_id,
            'seed_artists': artist_id,
            'limit': 10
        }

        # Параметры для запроса рекомендаций
        if request.form.get('use_loudness'):
            params['min_loudness'] = request.form.get('loudness')

        if request.form.get('use_danceability'):
            params['min_danceability'] = request.form.get('danceability')

        if request.form.get('use_energy'):
            params['min_energy'] = request.form.get('energy')

        if request.form.get('use_tempo'):
            params['min_tempo'] = request.form.get('tempo')

        if request.form.get('use_popularity'):
            params['target_popularity'] = request.form.get('popularity')

        if request.form.get('use_acousticness'):
            params['min_acousticness'] = request.form.get('acousticness')

        if request.form.get('use_instrumentalness'):
            params['min_instrumentalness'] = request.form.get('instrumentalness')

        if request.form.get('use_liveness'):
            params['min_liveness'] = request.form.get('liveness')

        if request.form.get('use_speechiness'):
            params['min_speechiness'] = request.form.get('speechiness')

        if request.form.get('use_valence'):
            params['min_valence'] = request.form.get('valence')

        print(f"Final request params: {params}")

        recommendations_url = f"https://api.spotify.com/v1/recommendations"
        response = requests.get(recommendations_url, headers=headers, params=params)

        if response.status_code == 200:
            recommendations = response.json().get('tracks')
            track_ids_only = [track['id'] for track in recommendations]
            session['recommended_tracks'] = None
            session['recommended_tracks'] = track_ids_only
            return render_template('recommendations.html', recommendations=recommendations)
        else:
            flash(f"Error fetching recommendations: {response.status_code}", 'error')
            return redirect(url_for('profile'))

    return render_template('customize_recommendations.html')
