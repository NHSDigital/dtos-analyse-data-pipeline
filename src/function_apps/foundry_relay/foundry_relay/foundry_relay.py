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
        logger.warning("No valid payloads in this batch.")
        return

    # Helper to split into chunks of 10
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    for chunk in chunks(batch_payloads, 10):
        file_name = generate_file_name()
        content = json.dumps(chunk, indent=2)
        upload_destinations = []

        # Upload to Foundry (if not skipped)
        skip_foundry_upload = (
            os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"
        )
        if not skip_foundry_upload:
            try:
                foundry_url = os.getenv("FOUNDRY_API_URL")
                api_token = os.getenv("FOUNDRY_API_TOKEN")
                parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
                if not foundry_url or not api_token or not parent_folder_rid:
                    raise EnvironmentError("Foundry environment variables are missing.")
                client = FoundryClient(
                    auth=UserTokenAuth(api_token), hostname=foundry_url
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
                logger.info(f"Batch file '{file_name}' uploaded to Foundry.")
                upload_destinations.append("Foundry")
            except Exception as foundry_error:
                logger.error(f"Failed to upload batch to Foundry: {foundry_error}")

        # Upload to Azurite Blob Storage
        try:
            azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
            azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
            if not azurite_connection_string or not azurite_container_name:
                raise EnvironmentError("Azurite Blob Storage configuration is missing.")
            blob_service_client = BlobServiceClient.from_connection_string(
                azurite_connection_string
            )
            blob_client = blob_service_client.get_blob_client(
                container=azurite_container_name, blob=file_name
            )
            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
            logger.info(f"Batch file '{file_name}' uploaded to Azurite Blob Storage.")
            upload_destinations.append("Azurite Blob Storage")
        except Exception as blob_error:
            logger.error(
                f"Failed to upload batch to Azurite Blob Storage: {blob_error}"
            )

        logger.info(
            f"Batch file '{file_name}' uploaded to: {', '.join(upload_destinations)}."
        )


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"
