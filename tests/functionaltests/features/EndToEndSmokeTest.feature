Feature: End to end Smoke Test
  Scenario: Payload is successfully posted to Azurite
    Given the API is running
    When I POST payload from "payloads/sample_payload.json" to "/api/service_layer"
    Then the response should have status code "200"
    And the content of file uploaded to blob storage should match with the request payload
