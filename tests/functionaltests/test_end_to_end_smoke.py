from pytest_bdd import scenarios, given, when, then, parsers
import requests
import pytest
import json
import os
import time
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

scenarios('features/EndToEndSmokeTest.feature')

@pytest.fixture
def context():
    return {}

@given('the API is running')
def api_running():
    # Optionally, check if the API is up
    pass

@when(parsers.parse('I POST payload from "{payload_file}" to "{endpoint}"'))
def post_payload_from_file(context, payload_file, endpoint):
    # Build the full path to the payload file
    payload_path = os.path.join(os.path.dirname(__file__), payload_file)
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    url = f'http://localhost:7072{endpoint}'
    response = requests.post(url, json=payload)
    context['response'] = response


@then(parsers.parse('the response should have status code "{status_code:d}"'))
def check_status_code(context, status_code):
    assert context['response'].status_code == status_code

@then('the content of file uploaded to blob storage should match with the request payload')
def read_first_blob_from_container():
    connection_string = os.getenv("AZURITE_CONNECTION_STRING")
    assert connection_string, "AZURITE_CONNECTION_STRING not set"

    azurite_local_connection_string = connection_string.replace("azurite", "localhost")

    blob_service_client = BlobServiceClient.from_connection_string(azurite_local_connection_string)
    container_client = blob_service_client.get_container_client("inbound")

    time.sleep(20)  # Wait for the file to be processed and uploaded to blob storage

    # Get the first blob in the container
    blobs = list(container_client.list_blobs())
    assert blobs, f"No blobs found in container inbound"
    first_blob_name = blobs[0].name

    # Download and read the blob content
    blob_client = container_client.get_blob_client(first_blob_name)
    blob_data = blob_client.download_blob().readall()
    content = blob_data.decode('utf-8')  # For text files

    data=json.loads(content)
    payload_path = os.path.join(os.path.dirname(__file__), 'payloads/sample_payload.json')
    with open(payload_path, 'r') as f:
        payload = json.load(f)

    assert payload == data[0], "File content from blob storage should match payload posted"
    return content
