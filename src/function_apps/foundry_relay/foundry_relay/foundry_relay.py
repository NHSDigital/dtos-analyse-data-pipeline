import json
import logging
import os
from datetime import datetime
from uuid import uuid4
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode
from azure.servicebus.exceptions import ServiceBusError
from azure.storage.blob import BlobServiceClient
from foundry_sdk import FoundryClient, UserTokenAuth

logger = logging.getLogger(__name__)


def main(foundryRelaySchedule: func.TimerRequest) -> None:
    logger.info("Foundry batch upload function triggered by Timer Schedule.")

    # Gather all environment variables at the top
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
    topic_name = os.getenv("TOPIC_NAME")
    subscription_name = os.getenv("SUBSCRIPTION_NAME")
    fully_qualified_namespace = os.getenv("SERVICE_BUS_NAMESPACE")
    connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
    batch_size = int(os.getenv("FOUNDRY_RELAY_N_RECORDS_PER_BATCH", "10"))
    foundry_url = os.getenv("FOUNDRY_API_URL")
    api_token = os.getenv("FOUNDRY_API_TOKEN")
    parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
    target_data_warehouse = os.getenv("TARGET_DATA_WAREHOUSE", "blob").lower()
    azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
    azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")

    # Determine auth mode
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"
    topic_name = os.getenv("TOPIC_NAME")

    if not topic_name:
        raise EnvironmentError("Service Bus topic name is missing.")

    # Create ServiceBusClient
    if use_managed_identity:
        if not fully_qualified_namespace:
            logger.error(
                "SERVICE_BUS_NAMESPACE is required when using managed identity."
            )
            return
        logger.info("Using Managed Identity for Service Bus authentication.")
        credential = DefaultAzureCredential()
        client = ServiceBusClient(
            fully_qualified_namespace=fully_qualified_namespace, credential=credential
        )
    else:
        if not connection_str:
            logger.error(
                "SERVICE_BUS_CONNECTION_STR is required when not using managed identity."
            )
            return
        logger.info("Using connection string for Service Bus authentication.")
        client = ServiceBusClient.from_connection_string(connection_str)

    try:
        with client:
            receiver = client.get_subscription_receiver(
                topic_name=topic_name, subscription_name=subscription_name
            )
            with receiver:
                logger.info(
                    f"Attempting to receive up to {batch_size} messages from topic '{topic_name}' and subscription '{subscription_name}'."
                )
                messages = receiver.receive_messages(
                    max_message_count=batch_size, max_wait_time=5
                )
                logger.info(f"Received {len(messages)} messages.")

                if not messages:
                    raise ValueError("No messages received from Service Bus.")

                batch_payloads = []
                for message in messages:
                    try:
                        body_bytes = b"".join(message.body)
                        payload = json.loads(body_bytes.decode("utf-8"))
                        batch_payloads.append(payload)
                        logger.info(f"Received message: {payload}")
                        receiver.complete_message(message)
                        logger.info("Message completed (removed from queue).")
                    except Exception as e:
                        logger.error(f"Error parsing or completing message: {e}")

                if not batch_payloads:
                    raise ValueError("No valid payloads to process.")

                file_name = generate_file_name()
                content = json.dumps(batch_payloads, indent=2)
                upload_destinations = []

                # Upload to Foundry Folder
                try:
                    if not foundry_url or not api_token or not parent_folder_rid:
                        raise EnvironmentError(
                            "Foundry environment variables are missing."
                        )
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
                    logger.info(f"File '{file_name}' uploaded to Foundry.")
                    upload_destinations.append("Foundry")
                except Exception as foundry_error:
                    logger.error(f"Failed to upload batch to Foundry: {foundry_error}")

                # Upload to Azurite Blob Storage (local only)
                if target_data_warehouse == "blob":
                    try:
                        if not azurite_connection_string or not azurite_container_name:
                            raise EnvironmentError(
                                "Azurite Blob configuration is missing."
                            )
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
                        logger.error(
                            f"Failed to upload batch to Azurite Blob: {blob_error}"
                        )

                logger.info(
                    f"File '{file_name}' uploaded to: {', '.join(upload_destinations)}."
                )

    except ServiceBusError as sb_err:
        logger.error(f"Service Bus error: {sb_err}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        raise


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"batch_{current_time}_{unique_suffix}.json"
