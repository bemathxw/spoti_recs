import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, session
from recommendations import recommendations_bp
from spotify import spotify_bp

@pytest.fixture
def client():
    
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.secret_key = 'testkey'
    app.register_blueprint(recommendations_bp, url_prefix='/recommendations')
    app.register_blueprint(spotify_bp, url_prefix='/spotify')

    @app.route('/')
    def home():
        return "Home Page"

    app.testing = True
    with app.test_client() as client:
        yield client

@patch('recommendations.get_headers')
@patch('recommendations.requests.get')
def test_customize_recommendations(mock_requests_get, mock_get_headers, client):
    
    mock_get_headers.return_value = {'Authorization': 'Bearer valid_token'}

    track_mock_response = MagicMock()
    track_mock_response.status_code = 200
    track_mock_response.json.return_value = {
        "artists": [{"id": "mock_artist_id", "name": "Mock Artist"}]
    }

    recommendations_mock_response = MagicMock()
    recommendations_mock_response.status_code = 200
    recommendations_mock_response.json.return_value = {
        "tracks": [
            {
                "album": {"images": [{"url": "https://i.scdn.co/image/mock_album_image.jpg"}], "name": "Mock Album"},
                "artists": [{"id": "mock_artist_id", "name": "Mock Artist"}],
                "id": "mock_track_id",
                "name": "Mock Track 1"
            }
        ]
    }

    mock_requests_get.side_effect = [track_mock_response, recommendations_mock_response]

    with client.session_transaction() as sess:
        sess['spotify_token'] = 'valid_token'
        sess['spotify_token_expires_in'] = 9999999999

    response = client.post('/recommendations/customize-recommendations', data={
        'track_link': 'https://open.spotify.com/track/mocktrack',
        'use_energy': 'on',
        'energy': '0.8'
    })

    assert response.status_code == 200

    mock_requests_get.assert_any_call(
        "https://api.spotify.com/v1/tracks/mocktrack",
        headers={'Authorization': 'Bearer valid_token'}
    )
    mock_requests_get.assert_any_call(
        "https://api.spotify.com/v1/recommendations",
        headers={'Authorization': 'Bearer valid_token'},
        params={
            'seed_tracks': 'mocktrack',
            'seed_artists': 'mock_artist_id',
            'limit': 10,
            'min_energy': '0.8'
        }
    )