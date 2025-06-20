import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from enum import Enum
from typing import List, Union, NoReturn, NamedTuple, Optional
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)


def get_env(key: str, default=None, required=False) -> Union[str, NoReturn]:
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value

class DataWarehouseTarget(Enum):
    FOUNDRY = "foundry"
    BLOB = "blob"


class FoundryEnv(NamedTuple):
    url: str
    token: str
    folder: str


class BlobEnv(NamedTuple):
    conn_str: str
    container: str


def load_foundry_env() -> FoundryEnv:
    return FoundryEnv(
        url=get_env("FOUNDRY_API_URL", required=True),
        token=get_env("FOUNDRY_API_TOKEN", required=True),
        folder=get_env("FOUNDRY_PARENT_FOLDER_RID", required=True),
    )


def load_blob_env() -> BlobEnv:
    return BlobEnv(
        conn_str=get_env("AZURITE_CONNECTION_STRING", required=True),
        container=get_env("AZURITE_CONTAINER_NAME", required=True),
    )


def get_data_warehouse_target(
    target_data_warehouse: Optional[str] = None,
) -> DataWarehouseTarget:
    if target_data_warehouse is None:
        target_data_warehouse = TARGET_DATA_WAREHOUSE
    try:
        return DataWarehouseTarget(target_data_warehouse)
    except ValueError:
        raise ValueError(
            f"Unsupported TARGET_DATA_WAREHOUSE value: {target_data_warehouse}"
        )


def write_to_foundry(
    file_name: str,
    content: str,
    foundry_url: str,
    api_token: str,
    parent_folder_rid: str,
) -> None:
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
) -> None:
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


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"


def main(serviceBusMessages: List[func.ServiceBusMessage]) -> None:
    global N_RECORDS_PER_BATCH
    N_RECORDS_PER_BATCH = int(get_env("FOUNDRY_RELAY_N_RECORDS_PER_BATCH",10))
    global TARGET_DATA_WAREHOUSE
    TARGET_DATA_WAREHOUSE = get_env("TARGET_DATA_WAREHOUSE", default="blob").lower()

    logger.info("Foundry batch upload function triggered by Service Bus.")
    target = get_data_warehouse_target()

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
    content = json.dumps(batch_payloads, indent=1)

    if target == DataWarehouseTarget.FOUNDRY:
        foundry_env = load_foundry_env()
        write_to_foundry(
            file_name,
            content,
            foundry_env.url,
            foundry_env.token,
            foundry_env.folder,
        )
    elif target == DataWarehouseTarget.BLOB:
        blob_env = load_blob_env()
        write_to_blob(
            file_name,
            content,
            blob_env.conn_str,
            blob_env.container,
        )
    else:
        raise ValueError(f"Unsupported TARGET_DATA_WAREHOUSE: {target}")
