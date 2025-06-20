import pytest
from unittest.mock import patch, MagicMock
import json
from http import HTTPStatus
import azure.functions as func
from function_apps.foundry_relay.foundry_relay import main


@pytest.fixture
def mock_request():
    """Fixture to create a mock HTTP request."""
    payload = {"key1": "value1", "key2": "value2"}
    return func.HttpRequest(
        method="POST",
        url="/api/FoundryRelayFunction",
        body=json.dumps(payload).encode("utf-8"),
        headers={},
    )


@pytest.fixture
def sample_message():
    payload = {"key1": "value1", "key2": "value2"}
    m = MagicMock()
    m.get_body.return_value = json.dumps(payload).encode("utf-8")
    return m


def test_happy_path_with_foundry_upload(monkeypatch, sample_message):
    """Test the main function for a successful file upload with Foundry upload enabled."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "foundry")
    monkeypatch.setenv("FOUNDRY_API_URL", "https://foundry.example.com")
    monkeypatch.setenv("FOUNDRY_API_TOKEN", "mock-token")
    monkeypatch.setenv("FOUNDRY_PARENT_FOLDER_RID", "mock-dataset-id")
    monkeypatch.setenv(
        "AZURITE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "mock-container")
    monkeypatch.setenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10")

    with patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.FoundryClient"
    ) as mock_foundry_client, patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient"
    ) as mock_blob_service_client:
        mock_client_instance = MagicMock()
        mock_foundry_client.return_value = mock_client_instance
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = (
            mock_blob_client
        )

        main([sample_message])
        mock_client_instance.datasets.Dataset.File.upload.assert_called_once()
        mock_blob_client.upload_blob.assert_not_called()


def test_happy_path_with_blob_upload(monkeypatch, sample_message):
    """Test the main function for a successful file upload with Blob upload enabled."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv(
        "AZURITE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "mock-container")
    monkeypatch.setenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10")

    with patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient"
    ) as mock_blob_service_client:
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = (
            mock_blob_client
        )

        main([sample_message])
        mock_blob_client.upload_blob.assert_called_once()


def test_main_missing_env_vars(monkeypatch, sample_message):
    """Test the main function when required environment variables are missing."""
    monkeypatch.delenv("TARGET_DATA_WAREHOUSE", raising=False)
    with pytest.raises(EnvironmentError):
        main([sample_message])


def test_main_invalid_payload(monkeypatch):
    """Test the main function with an invalid payload."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv(
        "AZURITE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "mock-container")
    monkeypatch.setenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10")

    invalid_message = MagicMock()
    invalid_message.get_body.return_value = b"invalid_payload"

    with pytest.raises(ValueError):
        main([invalid_message])


def test_main_foundry_upload_failure(monkeypatch, sample_message):
    """Test the main function when the Foundry upload fails."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "foundry")
    monkeypatch.setenv("FOUNDRY_API_URL", "https://foundry.example.com")
    monkeypatch.setenv("FOUNDRY_API_TOKEN", "mock-token")
    monkeypatch.setenv("FOUNDRY_PARENT_FOLDER_RID", "mock-dataset-id")
    monkeypatch.setenv(
        "AZURITE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "mock-container")
    monkeypatch.setenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10")

    with patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.FoundryClient"
    ) as mock_foundry_client:
        mock_client_instance = MagicMock()
        mock_client_instance.datasets.Dataset.create.return_value.rid = "mock-rid"
        mock_client_instance.datasets.Dataset.File.upload.side_effect = Exception(
            "Foundry upload failed"
        )
        mock_foundry_client.return_value = mock_client_instance

        with pytest.raises(Exception, match="Foundry upload failed"):
            main([sample_message])


def test_main_blob_upload_failure(monkeypatch, sample_message):
    """Test the main function when the Blob Storage upload fails."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv(
        "AZURITE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=mock-key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "mock-container")
    monkeypatch.setenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10")

    with patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient"
    ) as mock_blob_service_client:
        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = (
            mock_blob_client
        )
        mock_blob_client.upload_blob.side_effect = Exception("Blob upload failed")

        with pytest.raises(Exception, match="Blob upload failed"):
            main([sample_message])
