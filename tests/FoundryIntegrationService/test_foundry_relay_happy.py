# tests/test_foundry_relay_happy.py
"""
Light-weight unit tests for
src/function_apps/foundry_relay/foundry_relay.py

* All external calls (Azure / Foundry) are stubbed.
* Scenarios covered
  1. Utility helpers behave correctly
  2. Blob-only upload path
  3. Foundry + Blob upload path (cloud + local)
  4. Invalid JSON raises ValueError

► Expected overall coverage ≥ 80 %.
"""

from __future__ import annotations

import importlib
import json
from unittest.mock import patch, MagicMock

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Dynamic import – assumes PYTHONPATH contains “src”
# ──────────────────────────────────────────────────────────────────────────────
relay = importlib.import_module("function_apps.foundry_relay.foundry_relay")

main = relay.main
generate_file_name = relay.generate_file_name
get_data_warehouse_target = relay.get_data_warehouse_target


class FakeSB:
    """Minimal stub that mimics azure.functions.ServiceBusMessage."""

    def __init__(self, payload: dict | str):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self._body = payload.encode()

    def get_body(self):
        return self._body


# ───────────────────────────── utility helpers ──────────────────────────────


def test_generate_file_name_is_unique():
    """Two calls must return different values and both start with 'batch_'."""
    a = generate_file_name()
    b = generate_file_name()
    assert a != b
    assert a.startswith("batch_") and b.startswith("batch_")


def test_get_data_warehouse_target_default(monkeypatch: pytest.MonkeyPatch):
    """When the env var is absent, 'blob' is the default target."""
    monkeypatch.delenv("TARGET_DATA_WAREHOUSE", raising=False)
    assert get_data_warehouse_target().value == "blob"


# ───────────────────────────── main() scenarios ─────────────────────────────


@pytest.fixture()
def sample_msg() -> FakeSB:
    return FakeSB({"hello": "world"})


@patch("function_apps.foundry_relay.foundry_relay.FoundryClient")          # not used
@patch("function_apps.foundry_relay.foundry_relay.BlobServiceClient")
def test_blob_only_path(mock_blob, mock_foundry, monkeypatch: pytest.MonkeyPatch, sample_msg: FakeSB):
    """With TARGET_DATA_WAREHOUSE=blob the function writes only to blob."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    main([sample_msg])

    mock_blob.from_connection_string.assert_called_once()
    mock_foundry.assert_not_called()


@patch("function_apps.foundry_relay.foundry_relay.BlobServiceClient")
@patch("function_apps.foundry_relay.foundry_relay.FoundryClient")
def test_foundry_and_blob_success(mock_foundry, mock_blob, monkeypatch: pytest.MonkeyPatch, sample_msg: FakeSB):
    """Cloud path – Foundry upload succeeds; local dev also writes to blob."""
    # Foundry configuration
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "foundry")
    monkeypatch.setenv("FOUNDRY_API_URL", "https://example")
    monkeypatch.setenv("FOUNDRY_API_TOKEN", "token")
    monkeypatch.setenv("FOUNDRY_PARENT_FOLDER_RID", "rid")
    # ENVIRONMENT=local triggers the extra blob write
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    main([sample_msg])

    mock_foundry.assert_called_once()
    mock_blob.from_connection_string.assert_called_once()


@patch("function_apps.foundry_relay.foundry_relay.BlobServiceClient")
def test_invalid_json_raises(mock_blob, monkeypatch: pytest.MonkeyPatch):
    """A malformed JSON payload must raise ValueError and skip uploads."""
    monkeypatch.setenv("TARGET_DATA_WAREHOUSE", "blob")
    monkeypatch.setenv("AZURITE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    monkeypatch.setenv("AZURITE_CONTAINER_NAME", "inbound")

    bad_msg = FakeSB("not-json")

    with pytest.raises(ValueError):
        main([bad_msg])

    mock_blob.from_connection_string.assert_not_called()
