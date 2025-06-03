import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from typing import List
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)

# Environment Variable Name
ENV_VARS ={
    "ENV_FOUNDRY_URL" : os.getenv("FOUNDRY_API_URL"),
    "ENV_FOUNDRY_TOKEN" : os.getenv("FOUNDRY_API_TOKEN"),
    "ENV_FOUNDRY_PARENT_FOLDER_RID": os.getenv("FOUNDRY_PARENT_FOLDER_RID"),
    "ENV_AZURITE_CONNECTION_STRING": os.getenv("AZURITE_CONNECTION_STRING"),
    "ENV_AZURITE_CONTAINER_NAME": os.getenv("AZURITE_CONTAINER_NAME"),
    "FOUNDRY_RELAY_N_RECORDS_PER_BATCH": os.getenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10"),
    "TARGET_DATAWAREHOUSE": os.getenv("TARGET_DATAWAREHOUSE", "blob"),
}

def main(serviceBusMessages: List[func.ServiceBusMessage]) -> None:
    logger.info("Foundry batch upload function triggered by Service Bus.")

    if ENV_VARS["TARGET_DATAWAREHOUSE"] == "foundry":
        foundry_url = get_env("FOUNDRY_API_URL", required=True)
        api_token = get_env("FOUNDRY_API_TOKEN", required=True)
        parent_folder_rid = get_env("FOUNDRY_PARENT_FOLDER_RID", required=True)

    if ENV_VARS["TARGET_DATAWAREHOUSE"] == "blob":
        azurite_container_name = get_env("AZURITE_CONTAINER_NAME", required=True)
        azurite_connection_string = get_env("AZURITE_CONNECTION_STRING", required=True)

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

    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    # Get batch size from environment variable, default to 10 if not set
    batch_size = int(os.getenv(FOUNDRY_RELAY_N_RECORDS_PER_BATCH, "10"))

    for chunk in chunks(batch_payloads, batch_size):
        file_name = generate_file_name()
        content = json.dumps(chunk, indent=2)
        upload_destinations = []

        # Upload to Foundry Folder
        try:
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


        # Upload to local Azurite Blob if local development
        if get_env("TARGET_DATAWAREHOUSE", default="blob") == "blob":
            try:
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

def get_env(var_name, required=False, default=None):
    value = os.getenv(var_name, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required env var: {var_name}")
    return value
