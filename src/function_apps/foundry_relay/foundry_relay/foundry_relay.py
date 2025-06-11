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


def main(serviceBusMessages: List[func.ServiceBusMessage]) -> None:
    logger.info("Foundry batch upload function triggered by Service Bus.")
    logger.info(f"{len(serviceBusMessages)} messages have been read from Service Bus.")
    logger.info(
        f"FOUNDRY_RELAY_N_RECORDS_PER_BATCH: {FOUNDRY_RELAY_N_RECORDS_PER_BATCH}"
    )

    target = get_data_warehouse_target()
    logger.info(f"Using target: {target}")
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

    file_name = generate_file_name()
    content = json.dumps(batch_payloads, separators=(",", ":"))
    write_destinations = []

    if target == DataWarehouseTarget.FOUNDRY:
        if write_to_foundry(
            file_name, content, foundry_url, api_token, parent_folder_rid
        ):
            write_destinations.append("Foundry")
            logger.info(
                f"{len(batch_payloads)} messages written to Foundry in batch '{file_name}'."
            )

    if target == DataWarehouseTarget.BLOB:
        if write_to_blob(
            file_name, content, azurite_connection_string, azurite_container_name
        ):
            write_destinations.append("Azurite Blob")
            logger.info(
                f"{len(batch_payloads)} messages written to Azurite Blob in batch '{file_name}'."
            )
    logger.info(f"File '{file_name}' written to: {', '.join(write_destinations)}.")


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"


def get_env(var_name, required=False, default=None):
    value = os.getenv(var_name, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required env var: {var_name}")
    return value
