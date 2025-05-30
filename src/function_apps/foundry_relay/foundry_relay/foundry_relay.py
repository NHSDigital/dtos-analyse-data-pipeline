import json
import logging
import os
from datetime import datetime
from uuid import uuid4

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth
from azure.servicebus import ServiceBusClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()
logger = logging.getLogger(__name__)


@app.function_name(name="dev-uks-ap-foundry-relay")
@app.schedule(schedule="*/1 * * * *", arg_name="mytimer", run_on_startup=False, use_monitor=True)
def main(mytimer: func.TimerRequest) -> None:
    logger.info("Foundry file upload function triggered by Timer.")
    logging.info(f"Received message: {msg.get_body().decode()}")


    try:
        # Connect to Service Bus using Managed Identity
        with create_service_bus_client() as sb_client:
            receiver = sb_client.get_subscription_receiver(
                topic_name=os.getenv("SERVICE_BUS_TOPIC"),
                subscription_name=os.getenv("SERVICE_BUS_SUBSCRIPTION")
            )

            with receiver:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=10)
                if not messages:
                    logger.info("No messages found.")
                for serviceBusMessage in messages:
                    try:
                        logger.info("Processing Service Bus message...")
                        message_body = serviceBusMessage.body.decode("utf-8")
                        payload = json.loads(message_body)

                        process_payload(payload)

                        receiver.complete_message(serviceBusMessage)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        receiver.abandon_message(serviceBusMessage)

    except Exception as e:
        logger.error(f"Error during Service Bus polling: {e}", exc_info=True)
        raise


def process_payload(payload: dict):
    # Validate environment variables
    foundry_url = os.getenv("FOUNDRY_API_URL")
    api_token = os.getenv("FOUNDRY_API_TOKEN")
    parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
    azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
    azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
    skip_foundry_upload = (
        os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"
    )

    logger.info(f"SKIP_FOUNDRY_UPLOAD is set to: {skip_foundry_upload}")

    if not azurite_connection_string or not azurite_container_name:
        raise EnvironmentError("Azurite Blob Storage configuration is missing.")

    if not isinstance(payload, dict):
        logger.error("Invalid payload format. Expected a JSON object.")
        raise ValueError("Invalid payload format. Expected a JSON object.")

    file_name = generate_file_name()
    content = json.dumps(payload)
    upload_destinations = []

    if not skip_foundry_upload:
        try:
            if not foundry_url or not api_token or not parent_folder_rid:
                raise EnvironmentError("Required Foundry environment variables are missing.")

            logger.info(f"Uploading file '{file_name}' to Foundry...")
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

            logger.info(f"Uploaded to Foundry: {dataset.rid}")
            upload_destinations.append("Foundry")
        except Exception as foundry_error:
            logger.error(f"Failed to upload to Foundry: {foundry_error}")
            raise RuntimeError("Foundry upload failed.") from foundry_error
    else:
        logger.info("Skipping Foundry upload as configured.")

    try:
        logger.info(f"Uploading file '{file_name}' to Azurite...")
        blob_service_client = BlobServiceClient.from_connection_string(azurite_connection_string)
        blob_client = blob_service_client.get_blob_client(
            container=azurite_container_name, blob=file_name
        )
        blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
        logger.info("Uploaded to Azurite successfully.")
        upload_destinations.append("Azurite")
    except Exception as blob_error:
        logger.error(f"Failed to upload to Azurite: {blob_error}")
        raise RuntimeError("Azurite upload failed.") from blob_error

    logger.info(f"File uploaded to: {', '.join(upload_destinations)}")


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"{current_time}_{unique_suffix}.json"


def create_service_bus_client() -> ServiceBusClient:
    logger.info("Using Managed Identity for Service Bus access.")
    fully_qualified_namespace = os.getenv("SERVICE_BUS_NAMESPACE")
    if not fully_qualified_namespace:
        raise EnvironmentError("SERVICE_BUS_NAMESPACE must be set.")
    credential = DefaultAzureCredential()
    return ServiceBusClient(fully_qualified_namespace=fully_qualified_namespace, credential=credential)
