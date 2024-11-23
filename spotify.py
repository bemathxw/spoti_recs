import requests
import time
from flask import Blueprint, redirect, request, session, url_for, flash, render_template
from urllib.parse import urlencode

spotify_bp = Blueprint('spotify', __name__)

# Spotify OAuth2 настройки
SPOTIFY_CLIENT_ID = "432705662cc1443baa6faf1fa22171a2"
SPOTIFY_CLIENT_SECRET = "64824fc6b85e4bbd9740808743442d8c"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/spotify/callback"

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SCOPE = "user-read-private user-read-email user-top-read playlist-modify-private"
SHOW_DIALOG = "true"

@spotify_bp.route('/clear')
def clear_spotify_tokens():
    """Очищаем все токены Spotify из сессии"""
    session.pop('spotify_token', None)
    session.pop('spotify_refresh_token', None)
    session.pop('spotify_token_expires_in', None)
    print("Spotify tokens cleared from session.")
    return redirect('profile')


def is_token_expired():
    expires_at = session.get('spotify_token_expires_in')
    return expires_at and time.time() > expires_at


def refresh_spotify_token():
    """Обновляем access_token с помощью refresh_token"""
    refresh_token = session.get('spotify_refresh_token')

    if not refresh_token:
        print("No refresh token available. Clearing session and redirecting to login.")
        clear_spotify_tokens()
        return redirect(url_for('spotify.login_spotify'))

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload)
    response_data = response.json()

    if response.status_code != 200:
        print(f"Failed to refresh token: {response_data}. Clearing session and redirecting to login.")
        clear_spotify_tokens()
        return False

    # Обновляем токен в сессии
    session['spotify_token'] = response_data['access_token']
    session['spotify_token_expires_in'] = time.time() + response_data['expires_in']
    print("Token refreshed successfully.")
    return True


def get_headers():
    """Возвращаем заголовки с токеном для Spotify API, обновляем токен при необходимости"""
    if 'spotify_token' not in session:
        print("No token found in session, redirecting to login.")
        return None

    if is_token_expired():
        print("Token expired, attempting to refresh...")
        if not refresh_spotify_token():
            print("Failed to refresh token, clearing session and redirecting to login.")
            clear_spotify_tokens()
            return None

    return {
        'Authorization': f"Bearer {session.get('spotify_token')}"
    }


@spotify_bp.route('/login-spotify')
def login_spotify():
    auth_query_parameters = {
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPE,
        "client_id": SPOTIFY_CLIENT_ID,
        "show_dialog": SHOW_DIALOG
    }
    url_args = urlencode(auth_query_parameters)
    auth_url = f"{SPOTIFY_AUTH_URL}/?{url_args}"
    return redirect(auth_url)


@spotify_bp.route('/spotify/callback')
def callback():
    auth_token = request.args.get('code')

    if not auth_token:
        flash("Authorization failed. No code provided.", "error")
        return redirect(url_for('profile'))

    payload = {
        "grant_type": "authorization_code",
        "code": auth_token,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(SPOTIFY_TOKEN_URL, data=payload)
    response_data = response.json()

    if response.status_code != 200:
        flash(f"Failed to authenticate with Spotify: {response_data}", "error")
        return redirect(url_for('profile'))

    # Сохраняем токен в сессии
    session['spotify_token'] = response_data['access_token']
    session['spotify_refresh_token'] = response_data.get('refresh_token')
    session['spotify_token_expires_in'] = time.time() + response_data['expires_in']

    # Перенаправляем на страницу рекомендаций
    return redirect(url_for('spotify.spotify_recommendations'))



def get_top_tracks():
    headers = get_headers()
    if not headers:
        print("No headers found, returning empty list")
        return []

    top_tracks_url = f"{SPOTIFY_API_BASE_URL}/me/top/tracks?limit=10&time_range=short_term"
    response = requests.get(top_tracks_url, headers=headers)

    if response.status_code == 401:
        print("Token expired, refreshing...")
        if refresh_spotify_token():
            headers = get_headers()
            response = requests.get(top_tracks_url, headers=headers)

    if response.status_code == 200:
        print(f"Top tracks response: ok")
        return response.json().get('items')
    else:
        print(f"Error fetching top tracks: {response.status_code}, {response.text}")
        return []




# Получение рекомендаций на основе треков пользователя
def get_recommendations(track_ids):
    """Получаем рекомендации на основе треков пользователя"""
    headers = get_headers()
    if not headers:
        return [] 

    # Ограничиваем количество seed_tracks до 5
    track_ids = track_ids[:5]
    seed_tracks = ','.join(track_ids)
    recommendations_url = f"{SPOTIFY_API_BASE_URL}/recommendations?seed_tracks={seed_tracks}&limit=10"

    response = requests.get(recommendations_url, headers=headers)

    if response.status_code == 200:
        tracks = response.json().get('tracks')
        track_ids_only = [track['id'] for track in tracks]
        session['recommended_tracks'] = None
        session['recommended_tracks'] = track_ids_only
        return tracks

    else:
        print(f"Error fetching recommendations: {response.status_code}, {response.text}")
        return []


@spotify_bp.route('/spotify/recommendations')
def spotify_recommendations():

    if 'spotify_token' not in session:
        flash("You need to log in with Spotify to get recommendations.", "error")
        return redirect(url_for('spotify.login_spotify'))

    top_tracks = get_top_tracks()

    if not top_tracks:
        flash("Failed to get your top tracks from Spotify.", "error")
        return redirect(url_for('profile'))

    track_ids = [track['id'] for track in top_tracks]

    recommendations = get_recommendations(track_ids)

    print(session.get('recommended_tracks', []))
    print(session.get('recommended_tracks'))

    return render_template('profile.html', top_tracks=top_tracks, recommendations=recommendations)

@spotify_bp.route('/spotify/add_recommendations_to_queue', methods=['POST'])
def add_recommendations_to_queue():
    if is_premium_user():

        if 'spotify_token' not in session:
            flash("You need to log in with Spotify to add tracks to your queue.", "error")
            return redirect(url_for('spotify.login_spotify'))

        top_tracks = get_top_tracks()
        track_ids = [track['id'] for track in top_tracks]

        recommendations = get_recommendations(track_ids)
        if not recommendations:
            flash("No recommendations available to add.", "error")
            return redirect(url_for('profile'))

        headers = get_headers()
        if not headers:
            flash("Failed to authenticate with Spotify.", "error")
            return redirect(url_for('spotify.login_spotify'))

        for track in recommendations:
            track_uri = f"spotify:track:{track['id']}"
            queue_url = f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}"

            response = requests.post(queue_url, headers=headers)
            if response.status_code != 204:
                print(f"Failed to add track {track['name']} to the queue: {response.status_code}, {response.text}")
            else:
                print(f"Track {track['name']} successfully added to the queue.")

        flash("All recommended tracks added to your queue!", "success")
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('profile'))

def is_premium_user():

    user_profile_url = "https://api.spotify.com/v1/me"
    headers = get_headers()
    response = requests.get(user_profile_url, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return user_data.get('product') == 'premium'
    else:
        print(f"Failed to fetch user profile: {response.status_code}, {response.text}")
        return False

def create_playlist(headers):
    user_data = get_current_user(headers)
    if not user_data:
        return None

    user_id = user_data.get('id')
    create_playlist_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    playlist_name = "Saved recommendations"
    payload = {
        "name": playlist_name,
        "description": "Playlist created from your saved recommendations",
        "public": False
    }

    print(f"Creating playlist with name: {playlist_name} for user {user_id}")

    response = requests.post(create_playlist_url, json=payload, headers=headers)
    if response.status_code == 201:
        playlist_id = response.json()['id']
        print(f"Playlist created successfully: {playlist_id}")
        return playlist_id
    else:
        print(f"Error creating playlist: {response.status_code}, {response.text}")
        return None


def add_tracks_to_playlist(playlist_id, track_uris, headers):
    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    payload = {
        "uris": track_uris
    }

    print(f"Adding tracks to playlist {playlist_id}: {track_uris}")

    response = requests.post(add_tracks_url, json=payload, headers=headers)
    if response.status_code == 201:
        print("Tracks successfully added to playlist!")
    else:
        print(f"Error adding tracks to playlist: {response.status_code}, {response.text}")


@spotify_bp.route('/add-to-playlist', methods=['POST'])
def add_to_playlist():
    headers = get_headers()

    user_data = get_current_user(headers)
    if not user_data:
        print("Failed to get user profile.")
        return redirect(url_for('profile'))

    user_id = user_data.get('id')

    recommended_track_ids = session.get('recommended_tracks', [])
    if not recommended_track_ids:
        print("No recommended tracks available.")
        return redirect(url_for('profile'))

    playlist_id = create_playlist(headers)
    if playlist_id:
        
        track_uris = [f"spotify:track:{track_id}" for track_id in recommended_track_ids]
        add_tracks_to_playlist(playlist_id, track_uris, headers)
        print(f"Tracks added to playlist: {playlist_id}")
    else:
        print("Failed to create playlist.")

    return redirect(url_for('profile'))



def get_current_user(headers):
    user_profile_url = f"{SPOTIFY_API_BASE_URL}/me"
    response = requests.get(user_profile_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user profile: {response.status_code}, {response.text}")
        return None
