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

logger = logging.getLogger(__name__)


# === ENV Tools ===
def get_env(key: str, default=None, required=False):
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value


N_RECORDS_PER_BATCH = int(get_env("FOUNDRY_RELAY_N_RECORDS_PER_BATCH"))
TARGET_DATA_WAREHOUSE = get_env("TARGET_DATA_WAREHOUSE", default="blob").lower()


def load_foundry_env():
    return {
        "url": get_env("FOUNDRY_API_URL", required=True),
        "token": get_env("FOUNDRY_API_TOKEN", required=True),
        "folder": get_env("FOUNDRY_PARENT_FOLDER_RID", required=True),
    }


def load_blob_env():
    return {
        "conn_str": get_env("AZURITE_CONNECTION_STRING", required=True),
        "container": get_env("AZURITE_CONTAINER_NAME", required=True),
    }


# === Enums & Target Detection ===
class DataWarehouseTarget(Enum):
    FOUNDRY = "foundry"
    BLOB = "blob"


def get_data_warehouse_target() -> DataWarehouseTarget:
    try:
        return DataWarehouseTarget(TARGET_DATA_WAREHOUSE)
    except ValueError:
        raise ValueError(
            f"Unsupported TARGET_DATA_WAREHOUSE value: {TARGET_DATA_WAREHOUSE}"
        )


# === Writer Functions ===
def write_to_foundry(
    file_name: str,
    content: str,
    foundry_url: str,
    api_token: str,
    parent_folder_rid: str,
):
    try:
        client = FoundryClient(
            auth=UserTokenAuth(api_token),
            hostname=foundry_url,
        )
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
    except Exception as foundry_error:
        logger.error(f"Failed to write batch to Foundry: {foundry_error}")
        raise


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
    except Exception as blob_error:
        logger.error(f"Failed to write batch to Azurite Blob: {blob_error}")
        raise


# === Main Function ===
def main(serviceBusMessages: List[func.ServiceBusMessage]) -> None:
    logger.info("Foundry batch upload function triggered by Service Bus.")
    target = get_data_warehouse_target()

    # Read and parse all valid messages
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

    try:
        if target == DataWarehouseTarget.FOUNDRY:
            env = load_foundry_env()
            write_to_foundry(
                file_name, content, env["url"], env["token"], env["folder"]
            )
        elif target == DataWarehouseTarget.BLOB:
            env = load_blob_env()
            write_to_blob(
                file_name,
                content,
                env["conn_str"],
                env["container"],
            )
        else:
            raise ValueError(f"Unsupported TARGET_DATA_WAREHOUSE: {target}")
    except Exception as e:
        logger.error(f"Failed to write to an unknown destination: {e}")
        raise


# === Utility ===
def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"
