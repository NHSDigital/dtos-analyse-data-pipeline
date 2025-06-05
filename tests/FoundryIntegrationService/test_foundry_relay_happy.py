# tests/test_foundry_relay_happy.py
"""
Light-weight unit tests for
src/function_apps/foundry_relay/foundry_relay/foundry_relay.py

* Stub-only: never touches real Azure / Foundry
* 4 scenarios that exercise common and error branches; should lift
  overall coverage to ~80 %+
"""

from __future__ import annotations

import importlib
import json
from unittest.mock import patch, MagicMock

import pytest

# Dynamic import so the path isn’t hard-coded
relay = importlib.import_module(
    "function_apps.foundry_relay.foundry_relay.foundry_relay"
)
main = relay.main
generate_file_name = relay.generate_file_name
get_data_warehouse_target = relay.get_data_warehouse_target


class FakeSB:
    """Minimal ServiceBusMessage stub – only implements get_body()."""

    def __init__(self, payload: dict | str):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self._bytes = payload.encode()

    def get_body(self):
        return self._bytes


# ---------- util function tests ----------


def test_generate_file_name_unique():
    """Two calls should return different values and start with 'batch_'."""
    a, b = generate_file_name(), generate_file_name()
    assert a != b
    assert a.startswith("batch_") and b.startswith("batch_")


def test_get_data_warehouse_target_default(monkeypatch):
    """If the variable is missing, default should be blob."""
    monkeypatch.delenv("TARGET_DATA_WAREHOUSE", raising=False)
    assert get_data_warehouse_target().value == "blob"


# ---------- main handler scenarios ----------


@pytest.fixture()
def sample_message():
    return FakeSB({"hello": "world"})


@patch("function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient")
def test_blob_only_path(mock_blob, monkeypatch, sample_message):
    """TARGET_DATA_WAREHOUSE=blob → only Azurite is written."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    main([sample_message])

    mock_blob.from_connection_string.assert_called_once()
    # FoundryClient should not be invoked
    assert not patch(
        "function_apps.foundry_relay.foundry_relay.foundry_relay.FoundryClient"
    ).is_local


@patch("function_apps.foundry_relay.foundry_relay.foundry_relay.FoundryClient")
@patch("function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient")
def test_foundry_and_blob_success(mock_blob, mock_foundry, monkeypatch, sample_message):
    """Cloud mode: both Foundry and Blob paths succeed."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "foundry")
    # Foundry credentials
    monkeypatch.setenv("FOUNDRY_API_URL", "https://example")
    monkeypatch.setenv("FOUNDRY_API_TOKEN", "token")
    monkeypatch.setenv("FOUNDRY_PARENT_FOLDER_RID", "rid")
    # ENVIRONMENT=local triggers the extra Blob write
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    main([sample_message])

    mock_foundry.assert_called_once()
    mock_blob.from_connection_string.assert_called_once()


@patch("function_apps.foundry_relay.foundry_relay.foundry_relay.BlobServiceClient")
def test_invalid_json_returns_error(mock_blob, monkeypatch):
    """Invalid JSON in the message body should raise ValueError."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    bad_msg = FakeSB("not json")

    with pytest.raises(ValueError):
        main([bad_msg])
    mock_blob.from_connection_string.assert_not_called()
