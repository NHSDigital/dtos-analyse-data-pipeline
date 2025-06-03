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

<<<<<<< HEAD
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

=======
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
    target = get_data_warehouse_target()
    if target == DataWarehouseTarget.FOUNDRY:
        foundry_url = get_env("FOUNDRY_API_URL", required=True)
        api_token = get_env("FOUNDRY_API_TOKEN", required=True)
        parent_folder_rid = get_env("FOUNDRY_PARENT_FOLDER_RID", required=True)
    elif target == DataWarehouseTarget.BLOB:
        azurite_container_name = get_env("AZURITE_CONTAINER_NAME", required=True)
        azurite_connection_string = get_env("AZURITE_CONNECTION_STRING", required=True)
    else:
        raise ValueError(f"Unsupported TARGET_DATA_WAREHOUSE: {target}")
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
<<<<<<< HEAD
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
=======

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    batch_size = int(os.getenv(FOUNDRY_RELAY_N_RECORDS_PER_BATCH, "10"))

    target = os.getenv(ENV_TARGET_DW, "foundry").lower()
    if target == "blob_storage":
        writer = DataWarehouseBlobWriter()
    else:
        writer = DataWarehouseCloudWriter()

    writer.setup()
    for chunk in chunks(batch_payloads, batch_size):
        file_name = generate_file_name()
        content = json.dumps(chunk, indent=2)
        upload_destinations = []

        # Upload to Foundry Folder
        try:
            foundry_url = os.getenv(ENV_FOUNDRY_URL)
            api_token = os.getenv(ENV_FOUNDRY_TOKEN)
            parent_folder_rid = os.getenv(ENV_FOUNDRY_PARENT_FOLDER_RID)
            if not foundry_url or not api_token or not parent_folder_rid:
                raise EnvironmentError("Foundry environment variables are missing.")
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
            logger.info(f"File '{file_name}' uploaded to Foundry.")
            upload_destinations.append("Foundry")
        except Exception as foundry_error:
            logger.error(f"Failed to upload batch to Foundry: {foundry_error}")

        # Read ENVIRONMENT variable (default to 'cloud' if not set)
        environment = os.getenv("ENVIRONMENT", "cloud").lower()

        # Upload to local Azurite Blob if local development
        if environment == "local":
            try:
                azurite_connection_string = os.getenv(ENV_AZURITE_CONNECTION_STRING)
                azurite_container_name = os.getenv(ENV_AZURITE_CONTAINER_NAME)
                if not azurite_connection_string or not azurite_container_name:
                    raise EnvironmentError("Azurite Blob configuration is missing.")
                blob_service_client = BlobServiceClient.from_connection_string(
                    azurite_connection_string
                )
                blob_client = blob_service_client.get_blob_client(
                    container=azurite_container_name, blob=file_name
                )
                blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
                logger.info(f"File '{file_name}' uploaded to Azurite Blob.")
                upload_destinations.append("Azurite Blob")
            except Exception as blob_error:
                logger.error(f"Failed to upload batch to Azurite Blob: {blob_error}")

        logger.info(
            f"File '{file_name}' uploaded to: {', '.join(upload_destinations)}."
        )


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"
