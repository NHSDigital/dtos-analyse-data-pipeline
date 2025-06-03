import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from typing import List
from enum import Enum
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth
from typing import List

logger = logging.getLogger(__name__)

# Environment Variable Name
FOUNDRY_API_URL = os.getenv("FOUNDRY_API_URL")
FOUNDRY_API_TOKEN = os.getenv("FOUNDRY_API_TOKEN")
FOUNDRY_PARENT_FOLDER_RID = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
AZURITE_CONNECTION_STRING = os.getenv("AZURITE_CONNECTION_STRING")
AZURITE_CONTAINER_NAME = os.getenv("AZURITE_CONTAINER_NAME")
FOUNDRY_RELAY_N_RECORDS_PER_BATCH = os.getenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH")
class DataWarehouseTarget(Enum):
    FOUNDRY = "foundry"
    BLOB = "blob"

def get_data_warehouse_target() -> DataWarehouseTarget:
    value = os.getenv("TARGET_DATA_WAREHOUSE", "blob").lower()
    try:
        return DataWarehouseTarget(value)
    except ValueError:
        raise ValueError(f"Unsupported TARGET_DATA_WAREHOUSE value: {value}")

def write_to_foundry(
    file_name: str,
    content: str,
    foundry_url: str,
    api_token: str,
    parent_folder_rid: str,
):
    try:
        client = FoundryClient(auth=UserTokenAuth(api_token), hostname=foundry_url)
        dataset_name = file_name.replace(".json", "")
        dataset = client.datasets.Dataset.create(
            name=dataset_name, parent_folder_rid=parent_folder_rid
        )
        client.datasets.Dataset.File.upload(
            dataset_rid=dataset.rid,
            file_path=file_name,
            body=content.encode("utf-8"),
        )
        logger.info(f"File '{file_name}' written to Foundry.")
        return True
    except Exception as foundry_error:
        logger.error(f"Failed to write batch to Foundry: {foundry_error}")
        return False


def write_to_blob(
    file_name: str,
    content: str,
    azurite_connection_string: str,
    azurite_container_name: str,
):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            azurite_connection_string
        )
        blob_client = blob_service_client.get_blob_client(
            container=azurite_container_name, blob=file_name
        )
        blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
        logger.info(f"File '{file_name}' written to Azurite Blob.")
        return True
    except Exception as blob_error:
        logger.error(f"Failed to write batch to Azurite Blob: {blob_error}")
        return False


# Environment Variable Names
ENV_FOUNDRY_URL = "FOUNDRY_API_URL"
ENV_FOUNDRY_TOKEN = "FOUNDRY_API_TOKEN"
ENV_FOUNDRY_PARENT_FOLDER_RID = "FOUNDRY_PARENT_FOLDER_RID"
ENV_AZURITE_CONNECTION_STRING = "AZURITE_CONNECTION_STRING"
ENV_AZURITE_CONTAINER_NAME = "AZURITE_CONTAINER_NAME"
ENV_TARGET_DW = "TARGET_DATA_WAREHOUSE"
FOUNDRY_RELAY_N_RECORDS_PER_BATCH = "FOUNDRY_RELAY_N_RECORDS_PER_BATCH"


def main(serviceBusMessages: List[func.ServiceBusMessage]) -> None:
    logger.info("Foundry batch upload function triggered by Service Bus.")

    batch_payloads = []
    for serviceBusMessage in serviceBusMessages:
        try:
            message_body = serviceBusMessage.get_body().decode("utf-8")
            payload = json.loads(message_body)
            batch_payloads.append(payload)
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
    if not batch_payloads:
        raise ValueError("No valid payloads to process.")

    file_name = generate_file_name()
    content = json.dumps(batch_payloads, indent=2)
    write_destinations = []
    if target == DataWarehouseTarget.FOUNDRY:
        if write_to_foundry(
            file_name, content, foundry_url, api_token, parent_folder_rid
        ):
            write_destinations.append("Foundry")
    if target == DataWarehouseTarget.BLOB:
        if write_to_blob(
            file_name, content, azurite_connection_string, azurite_container_name
        ):
            write_destinations.append("Azurite Blob")
    logger.info(f"File '{file_name}' written to: {', '.join(write_destinations)}.")


    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    # Get batch size from environment variable, default to 10 if not set
    batch_size = int(os.getenv(FOUNDRY_RELAY_N_RECORDS_PER_BATCH, "10"))

    for chunk in chunks(batch_payloads, batch_size):
        writer.write(chunk)
    writer.teardown()


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"


class DataWarehouseBlobWriter:
    def setup(self):
        self.connection_str = os.getenv(ENV_AZURITE_CONNECTION_STRING)
        self.container = os.getenv(ENV_AZURITE_CONTAINER_NAME)
        if not self.connection_str or not self.container:
            raise EnvironmentError("Azurite Blob configuration is missing.")
        self.client = BlobServiceClient.from_connection_string(self.connection_str)

    def write(self, chunk):
        file_name = generate_file_name()
        content = json.dumps(chunk, indent=2)
        blob_client = self.client.get_blob_client(container=self.container, blob=file_name)
        blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
        logger.info(f"File '{file_name}' uploaded to Azurite Blob.")

    def teardown(self):
        pass


class DataWarehouseCloudWriter:
    def setup(self):
        self.foundry_url = os.getenv(ENV_FOUNDRY_URL)
        self.api_token = os.getenv(ENV_FOUNDRY_TOKEN)
        self.parent_folder_rid = os.getenv(ENV_FOUNDRY_PARENT_FOLDER_RID)
        if not self.foundry_url or not self.api_token or not self.parent_folder_rid:
            raise EnvironmentError("Foundry environment variables are missing.")
        self.client = FoundryClient(auth=UserTokenAuth(self.api_token), hostname=self.foundry_url)

    def write(self, chunk):
        file_name = generate_file_name()
        dataset_name = file_name.replace(".json", "")
        content = json.dumps(chunk, indent=2)
        dataset = self.client.datasets.Dataset.create(
            name=dataset_name, parent_folder_rid=self.parent_folder_rid
        )
        self.client.datasets.Dataset.File.upload(
            dataset_rid=dataset.rid,
            file_path=file_name,
            body=content.encode("utf-8"),
        )
        logger.info(f"File '{file_name}' uploaded to Foundry.")

    def teardown(self):
        pass
