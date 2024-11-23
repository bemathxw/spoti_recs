from behave import given, when, then
from unittest.mock import patch, MagicMock

@given("the user is authenticated")
def step_user_authenticated(context):
    with context.client.session_transaction() as sess:
        sess['spotify_token'] = 'valid_token'
        sess['spotify_token_expires_in'] = 9999999999

@when('the user submits track link "{track_link}" with energy "{energy}"')
def step_submit_recommendations(context, track_link, energy):
    with patch('recommendations.get_headers') as mock_get_headers, \
         patch('recommendations.requests.get') as mock_requests_get:

        mock_get_headers.return_value = {'Authorization': 'Bearer valid_token'}

        # Mock ответа для трека
        track_mock_response = MagicMock()
        track_mock_response.status_code = 200

        # Здесь мы используем параметры из таблицы Examples
        if 'mocktrack' in track_link:
            track_mock_response.json.return_value = {
                "artists": [{"id": "mock_artist_id", "name": "Mock Artist"}]
            }
        elif 'anothermock' in track_link:
            track_mock_response.json.return_value = {
                "artists": [{"id": "another_mock_artist_id", "name": "Another Artist"}]
            }
        else:
            track_mock_response.json.return_value = {
                "artists": [{"id": "default_artist_id", "name": "Default Artist"}]
            }

        # Mock ответа для рекомендаций
        recommendations_mock_response = MagicMock()
        recommendations_mock_response.status_code = 200

        if energy == '0.8':
            recommendations_mock_response.json.return_value = {
                "tracks": [
                    {
                        "album": {
                            "images": [{"url": "https://i.scdn.co/image/mock_album_image.jpg"}],
                            "name": "Mock Album"
                        },
                        "artists": [{"id": "mock_artist_id", "name": "Mock Artist"}],
                        "id": "mock_track_id",
                        "name": "Mock Track 1"
                    }
                ]
            }
        elif energy == '0.5':
            recommendations_mock_response.json.return_value = {
                "tracks": [
                    {
                        "album": {
                            "images": [{"url": "https://i.scdn.co/image/another_mock_album_image.jpg"}],
                            "name": "Another Album"
                        },
                        "artists": [{"id": "another_mock_artist_id", "name": "Another Artist"}],
                        "id": "another_mock_track_id",
                        "name": "Another Mock Track"
                    }
                ]
            }
        else:
            recommendations_mock_response.json.return_value = {"tracks": []}

        # Настраиваем последовательность моков
        mock_requests_get.side_effect = [track_mock_response, recommendations_mock_response]

        # Отправляем POST-запрос
        context.response = context.client.post('/recommendations/customize-recommendations', data={
            'track_link': track_link,
            'use_energy': 'on',
            'energy': energy
        })

@then("the response status should be {status:d}")
def step_check_response_status(context, status):
    assert context.response.status_code == status, f"Expected status {status}, got {context.response.status_code}"

@then('the response should contain "{text}"')
def step_check_response_contains(context, text):
    response_text = context.response.data.decode('utf-8')
    print("Response data:", response_text)  # For debugging
    assert text in response_text, f"Expected to find '{text}' in response"
