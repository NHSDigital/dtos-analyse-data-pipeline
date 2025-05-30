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
import azure.functions as func
import os

app = func.FunctionApp()


logger = logging.getLogger(__name__)

@app.function_name(name="dev-uks-ap-foundry-relay")
@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name=os.getenv("TOPIC_NAME"),
    subscription_name=os.getenv("SUBSCRIPTION_NAME"),
    connection="SERVICE_BUS_NAMESPACE"  # Only the name of the app setting, no connection string needed
)
def main(serviceBusMessage: func.ServiceBusMessage) -> None:
    logger.info("Foundry file upload function triggered by Service Bus.")

    try:
        # Attempt to parse the JSON payload
        try:
            message_body = serviceBusMessage.get_body().decode("utf-8")
            payload = json.loads(message_body)
        except json.JSONDecodeError as json_error:
            logger.error("Invalid JSON payload.")
            raise ValueError("Invalid JSON payload.") from json_error

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

        # Conditionally upload to Foundry
        if not skip_foundry_upload:
            try:
                if not foundry_url or not api_token or not parent_folder_rid:
                    raise EnvironmentError(
                        "Required Foundry environment variables are missing."
                    )

                logger.info(
                    f"Uploading file '{file_name}' to Foundry (parent folder RID: {parent_folder_rid})..."
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
                logger.info(
                    f"File '{file_name}' uploaded to Foundry successfully. Dataset RID: {dataset.rid}"
                )
                upload_destinations.append("Foundry")
            except Exception as foundry_error:
                logger.error(f"Failed to upload file to Foundry: {foundry_error}")
                raise RuntimeError(
                    "Failed to upload file to Foundry."
                ) from foundry_error
        else:
            logger.info("Skipping Foundry upload as per configuration.")

        # Upload to Azurite Blob Storage
        try:
            logger.info(
                f"Uploading file '{file_name}' to Azurite Blob Storage container: {azurite_container_name}..."
            )
            blob_service_client = BlobServiceClient.from_connection_string(
                azurite_connection_string
            )
            blob_client = blob_service_client.get_blob_client(
                container=azurite_container_name, blob=file_name
            )

            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
            logger.info(
                f"File '{file_name}' uploaded to Azurite Blob Storage successfully."
            )
            upload_destinations.append("Azurite Blob Storage")
        except Exception as blob_error:
            logger.error(f"Failed to upload file to Azurite Blob Storage: {blob_error}")
            raise RuntimeError(
                "Failed to upload file to Azurite Blob Storage."
            ) from blob_error

        logger.info(
            f"File '{file_name}' uploaded successfully to: {', '.join(upload_destinations)}."
        )

        # Optionally: interact with Service Bus topic (send/peek/etc.)
        # Uncomment the block below if needed
        with create_service_bus_client() as sb_client:
            receiver = sb_client.get_subscription_receiver(
                topic_name=os.getenv("SERVICE_BUS_TOPIC"),
                subscription_name=os.getenv("SERVICE_BUS_SUBSCRIPTION")
            )
            with receiver:
                messages = receiver.receive_messages(max_message_count=1, max_wait_time=5)
                for msg in messages:
                    logger.info(f"Received message via SDK: {msg}")
                    receiver.complete_message(msg)

    except EnvironmentError as env_err:
        logger.error(f"Environment variables configuration error: {env_err}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise


def generate_file_name() -> str:
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_suffix = uuid4().hex[:8]
    return f"{current_time}_{unique_suffix}.json"


def create_service_bus_client() -> ServiceBusClient:
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true"

    if use_managed_identity:
        logger.info("Connecting to Service Bus via Managed Identity.")
        fully_qualified_namespace = os.getenv("SERVICE_BUS_NAMESPACE")
        if not fully_qualified_namespace:
            raise EnvironmentError("SERVICE_BUS_NAMESPACE is required when using managed identity.")
        credential = DefaultAzureCredential()
        return ServiceBusClient(fully_qualified_namespace=fully_qualified_namespace, credential=credential)
    else:
        logger.info("Connecting to Service Bus via connection string.")
        connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
        if not connection_str:
            raise EnvironmentError("SERVICE_BUS_CONNECTION_STR is required when not using managed identity.")
        return ServiceBusClient.from_connection_string(connection_str)