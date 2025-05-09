import json
import logging
import os
from datetime import datetime
from uuid import uuid4
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)

def main(serviceBusMessage: func.ServiceBusMessage) -> None:
    logger.info('Foundry file upload function triggered by Service Bus.')

    try:
        # Attempt to parse the JSON payload
        try:
            message_body = serviceBusMessage.get_body().decode("utf-8")
            payload = json.loads(message_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload.")
            return

        # Validate environment variables
        foundry_url = os.getenv("FOUNDRY_API_URL")
        api_token = os.getenv("FOUNDRY_API_TOKEN")
        dataset_rid = os.getenv("FOUNDRY_RESOURCE_ID")
        azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
        azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
        skip_foundry_upload = os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"

        logger.info(f"SKIP_FOUNDRY_UPLOAD is set to: {skip_foundry_upload}")

        if not azurite_connection_string or not azurite_container_name:
            raise EnvironmentError("Azurite Blob Storage configuration is missing.")

        if not isinstance(payload, dict):
            logger.error("Invalid payload format. Expected a JSON object.")
            return

        file_name = generate_file_name()
        content = json.dumps(payload)
        upload_destinations = []

        # Conditionally upload to Foundry
        if not skip_foundry_upload:
            try:
                if not foundry_url or not api_token or not dataset_rid:
                    raise EnvironmentError("Required Foundry environment variables are missing.")

                logger.info(f"Uploading file '{file_name}' to Foundry dataset resource ID: {dataset_rid}...")
                client = FoundryClient(
                    auth=UserTokenAuth(api_token),
                    hostname=foundry_url
                )
                client.datasets.Dataset.File.upload(
                    dataset_rid=dataset_rid,
                    file_path=file_name,
                    body=content.encode("utf-8")
                )
                logger.info(f"File '{file_name}' uploaded to Foundry successfully.")
                upload_destinations.append("Foundry")
            except Exception as foundry_error:
                logger.error(f"Failed to upload file to Foundry: {foundry_error}")
                return

        else:
            logger.info("Skipping Foundry upload as per configuration.")

        # Upload to Azurite Blob Storage
        try:
            logger.info(f"Uploading file '{file_name}' to Azurite Blob Storage container: {azurite_container_name}...")
            blob_service_client = BlobServiceClient.from_connection_string(azurite_connection_string)
            blob_client = blob_service_client.get_blob_client(container=azurite_container_name, blob=file_name)

            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
            logger.info(f"File '{file_name}' uploaded to Azurite Blob Storage successfully.")
            upload_destinations.append("Azurite Blob Storage")
        except Exception as blob_error:
            logger.error(f"Failed to upload file to Azurite Blob Storage: {blob_error}")
            return

        logger.info(f"File '{file_name}' uploaded successfully to: {', '.join(upload_destinations)}.")
    except EnvironmentError as env_err:
        logger.error(f"Environment variables configuration error: {env_err}")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"{current_time}_{unique_suffix}.json"
