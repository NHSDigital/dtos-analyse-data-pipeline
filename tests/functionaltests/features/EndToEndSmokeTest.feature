Feature: End to end Smoke Test
  Scenario: Payload is successfully posted to Azurite and FDP Sandbox
    Given the API is running
    When I POST payload from "payloads/sample_payload.json" to "/api/ServicebusRelayFunction"
    Then the response should have status code "200"
    #And the content of file uploaded to blob storage should match with the request payload
