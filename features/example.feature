Feature: Recommendations customization

  Scenario: Fetching recommendations with valid parameters
    Given the user is authenticated
    When the user submits track link "https://open.spotify.com/track/mocktrack" with energy "0.8"
    Then the response status should be 200
    And the response should contain "Mock Track 1"
    And the response should contain "Mock Artist"
