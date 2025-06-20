import pytest
from unittest.mock import patch, MagicMock
import json
from http import HTTPStatus
import azure.functions as func
from foundry_relay.foundry_relay.foundry_relay import main

@pytest.fixture
def mock_request():
    """Fixture to create a mock HTTP request."""
    payload = {"key1": "value1", "key2": "value2"}
    return func.HttpRequest(
        method="POST",
        url="/api/FoundryRelayFunction",
        body=json.dumps(payload).encode("utf-8"),
        headers={}
    )

def test_happy_path_with_foundry_upload(mock_request):
    """Test the main function for a successful file upload with Foundry upload enabled."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv, \
    patch("foundry_relay.foundry_relay.foundry_relay.FoundryClient") as mock_foundry_client, \
    patch("foundry_relay.foundry_relay.foundry_relay.BlobServiceClient") as mock_blob_service_client:

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "FOUNDRY_API_URL": "https://foundry.example.com",
            "FOUNDRY_API_TOKEN": "mock-token",
            "FOUNDRY_RESOURCE_ID": "mock-dataset-id",
            "AZURITE_CONNECTION_STRING": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURITE_CONTAINER_NAME": "mock-container",
            "SKIP_FOUNDRY_UPLOAD": "false"
        }.get(key, default)

        # Mock FoundryClient behavior
        mock_client_instance = MagicMock()
        mock_foundry_client.return_value = mock_client_instance

        # Mock BlobServiceClient behavior
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.OK
        assert "File '2025" in response.get_body().decode("utf-8")  # Match the dynamic file name prefix
        mock_client_instance.datasets.Dataset.File.upload.assert_called_once()
        mock_blob_client.upload_blob.assert_called_once_with(json.dumps({"key1": "value1", "key2": "value2"}).encode("utf-8"), overwrite=True)

def test_happy_path_skip_foundry_upload(mock_request):
    """Test the main function for a successful file upload with Foundry upload skipped."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv, \
    patch("foundry_relay.foundry_relay.foundry_relay.FoundryClient") as mock_foundry_client, \
    patch("foundry_relay.foundry_relay.foundry_relay.BlobServiceClient") as mock_blob_service_client:

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "FOUNDRY_API_URL": "https://foundry.example.com",
            "FOUNDRY_API_TOKEN": "mock-token",
            "FOUNDRY_RESOURCE_ID": "mock-dataset-id",
            "AZURITE_CONNECTION_STRING": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURITE_CONTAINER_NAME": "mock-container",
            "SKIP_FOUNDRY_UPLOAD": "true"
        }.get(key, default)

        # Mock BlobServiceClient behavior
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.OK
        assert "File '2025" in response.get_body().decode("utf-8")  # Match the dynamic file name prefix
        mock_blob_client.upload_blob.assert_called_once_with(json.dumps({"key1": "value1", "key2": "value2"}).encode("utf-8"), overwrite=True)
        mock_foundry_client.assert_not_called()

def test_main_missing_env_vars(mock_request):
    """Test the main function when environment variables are missing."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv:

        # Mock environment variables to return None
        mock_getenv.side_effect = lambda key, default=None: None

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "internal server error" in response.get_body().decode("utf-8")

def test_main_invalid_payload():
    """Test the main function with an invalid payload."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv:

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "FOUNDRY_API_URL": "https://foundry.example.com",
            "FOUNDRY_API_TOKEN": "mock-token",
            "FOUNDRY_RESOURCE_ID": "mock-dataset-id",
            "AZURITE_CONNECTION_STRING": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURITE_CONTAINER_NAME": "mock-container",
            "SKIP_FOUNDRY_UPLOAD": "false"
        }.get(key, default)

        # Create a mock request with an invalid payload
        invalid_payload = "invalid_payload"
        mock_request = func.HttpRequest(
            method="POST",
            url="/api/FoundryRelayFunction",
            body=invalid_payload.encode("utf-8"),
            headers={}
        )

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Invalid JSON payload" in response.get_body().decode("utf-8")
def test_main_foundry_upload_failure(mock_request):
    """Test the main function when the Foundry upload fails."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv, \
    patch("foundry_relay.foundry_relay.foundry_relay.FoundryClient") as mock_foundry_client:

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "FOUNDRY_API_URL": "https://foundry.example.com",
            "FOUNDRY_API_TOKEN": "mock-token",
            "FOUNDRY_RESOURCE_ID": "mock-dataset-id",
            "AZURITE_CONNECTION_STRING": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURITE_CONTAINER_NAME": "mock-container",
            "SKIP_FOUNDRY_UPLOAD": "false"
        }.get(key, default)

        # Mock FoundryClient behavior to raise an exception
        mock_client_instance = MagicMock()
        mock_client_instance.datasets.Dataset.File.upload.side_effect = Exception("Foundry upload failed")
        mock_foundry_client.return_value = mock_client_instance

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "Failed to upload file to Foundry" in response.get_body().decode("utf-8")
        mock_client_instance.datasets.Dataset.File.upload.assert_called_once()

def test_main_blob_upload_failure(mock_request):
    """Test the main function when the Blob Storage upload fails."""
    with patch("foundry_relay.foundry_relay.foundry_relay.os.getenv") as mock_getenv, \
    patch("foundry_relay.foundry_relay.foundry_relay.FoundryClient") as mock_foundry_client, \
    patch("foundry_relay.foundry_relay.foundry_relay.BlobServiceClient") as mock_blob_service_client:

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "FOUNDRY_API_URL": "https://foundry.example.com",
            "FOUNDRY_API_TOKEN": "mock-token",
            "FOUNDRY_RESOURCE_ID": "mock-dataset-id",
            "AZURITE_CONNECTION_STRING": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "AZURITE_CONTAINER_NAME": "mock-container",
            "SKIP_FOUNDRY_UPLOAD": "false"
        }.get(key, default)

        # Mock BlobServiceClient behavior to raise an exception
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        mock_blob_client.upload_blob.side_effect = Exception("Blob upload failed")

        # Call the function
        response = main(mock_request)

        # Assertions
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "Failed to upload file to Azurite Blob Storage" in response.get_body().decode("utf-8")
        mock_blob_client.upload_blob.assert_called_once()
