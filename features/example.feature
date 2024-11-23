Feature: Recommendations customization

  Scenario Outline: Fetching recommendations with valid parameters
    Given the user is authenticated
    When the user submits track link "<track_link>" with energy "<energy>"
    Then the response status should be 200
    And the response should contain "<expected_track_name>"
    And the response should contain "<expected_artist_name>"

  Examples:
    | track_link                                 | energy | expected_track_name    | expected_artist_name |
    | https://open.spotify.com/track/mocktrack   | 0.8    | Mock Track 1           | Mock Artist          | 
    | https://open.spotify.com/track/anothermock | 0.5    | Another Mock Track     | Another Artist       |
