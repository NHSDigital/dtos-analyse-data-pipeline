import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from typing import List

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient

from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)

def main(mytimer: func.TimerRequest) -> None:
    logger.info("Timer-triggered Foundry relay function started.")

    # Step 1: Connect to Service Bus using Managed Identity
    service_bus_namespace = os.getenv("SERVICE_BUS_NAMESPACE")
    topic_name = os.getenv("TOPIC_NAME")
    subscription_name = os.getenv("SUBSCRIPTION_NAME")
    if not service_bus_namespace or not topic_name or not subscription_name:
        raise EnvironmentError("SERVICE_BUS_NAMESPACE, TOPIC_NAME, or SUBSCRIPTION_NAME not set.")

    credential = DefaultAzureCredential()
    servicebus_client = ServiceBusClient(service_bus_namespace, credential)

    batch_payloads = []

    # Step 2: Pull messages
    try:
        with servicebus_client:
            receiver = servicebus_client.get_subscription_receiver(
                topic_name=topic_name,
                subscription_name=subscription_name,
                max_wait_time=5  # seconds
            )
            with receiver:
                messages = receiver.receive_messages(max_message_count=50)
                for msg in messages:
                    try:
                        message_body = msg.body.decode("utf-8")
                        payload = json.loads(message_body)
                        batch_payloads.append(payload)
                        receiver.complete_message(msg)
                    except Exception as e:
                        logger.error(f"Error parsing or completing message: {e}")
    except Exception as e:
        logger.error(f"Failed to pull messages from Service Bus: {e}")
        return

    if not batch_payloads:
        logger.info("No messages received from Service Bus.")
        return

    # Step 3: Process in chunks
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    batch_size = int(os.getenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10"))

    for chunk in chunks(batch_payloads, batch_size):
        file_name = generate_file_name()
        content = json.dumps(chunk, indent=2)
        upload_destinations = []

        # Upload to Foundry
        try:
            foundry_url = os.getenv("FOUNDRY_API_URL")
            api_token = os.getenv("FOUNDRY_API_TOKEN")
            parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
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

        # Upload to Azurite if local
        environment = os.getenv("ENVIRONMENT", "cloud").lower()
        if environment == "local":
            try:
                azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
                azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
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
