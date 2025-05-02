import json
import logging
import os
from datetime import datetime
from http import HTTPStatus
from uuid import uuid4
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Foundry file upload function triggered.')

    try:
        # Attempt to parse the JSON payload
        try:
            payload = req.get_json()
        except json.JSONDecodeError:
            return func.HttpResponse(
                "Invalid JSON payload.",
                status_code=HTTPStatus.BAD_REQUEST
            )

        # Validate environment variables
        foundry_url = os.getenv("FOUNDRY_API_URL")
        api_token = os.getenv("FOUNDRY_API_TOKEN")
        dataset_rid = os.getenv("FOUNDRY_RESOURCE_ID")
        azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
        azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
        skip_foundry_upload = os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"

        # Log the value of SKIP_FOUNDRY_UPLOAD
        logger.info(f"SKIP_FOUNDRY_UPLOAD is set to: {skip_foundry_upload}")


        if not azurite_connection_string or not azurite_container_name:
            raise EnvironmentError("Azurite Blob Storage configuration is missing.")

        if not isinstance(payload, dict):
            return func.HttpResponse(
                "Invalid payload format. Expected a JSON object.",
                status_code=HTTPStatus.BAD_REQUEST
            )

        file_name = generate_file_name()
        content = json.dumps(payload)

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
            except Exception as foundry_error:
                logger.error(f"Failed to upload file to Foundry: {foundry_error}")
                return func.HttpResponse(
                    "Failed to upload file to Foundry.",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        else:
            logger.info("Skipping Foundry upload as per configuration.")

        # Upload to Azurite Blob Storage
        try:
            logger.info(f"Uploading file '{file_name}' to Azurite Blob Storage container: {azurite_container_name}...")
            blob_service_client = BlobServiceClient.from_connection_string(azurite_connection_string)
            blob_client = blob_service_client.get_blob_client(container=azurite_container_name, blob=file_name)

            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
            logger.info(f"File '{file_name}' uploaded to Azurite Blob Storage successfully.")
        except Exception as blob_error:
            logger.error(f"Failed to upload file to Azurite Blob Storage: {blob_error}")
            return func.HttpResponse(
                "Failed to upload file to Azurite Blob Storage.",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )

        return func.HttpResponse(
            f"File '{file_name}' uploaded successfully.",
            status_code=HTTPStatus.OK
        )

    except EnvironmentError as env_err:
        logger.error(f"Environment variables configuration error: {env_err}")
        return func.HttpResponse(
            str(env_err),
            status_code=HTTPStatus.BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return func.HttpResponse(
            "An internal server error occurred.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"{current_time}_{unique_suffix}.json"
