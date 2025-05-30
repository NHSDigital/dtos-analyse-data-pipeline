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
    logger.info("Foundry file upload function triggered by Service Bus (batch).")

    for serviceBusMessage in serviceBusMessages:
        try:
            # 1) Parse JSON payload
            raw = serviceBusMessage.get_body().decode("utf-8")
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload; skipping message.")
            continue

        # 2) Validate env vars
        foundry_url = os.getenv("FOUNDRY_API_URL")
        api_token = os.getenv("FOUNDRY_API_TOKEN")
        parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
        azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
        azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
        skip_foundry_upload = os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"

        if not azurite_connection_string or not azurite_container_name:
            logger.error("Azurite Blob Storage configuration is missing; skipping message.")
            continue

        # 3) Generate file and content
        file_name = generate_file_name()
        content = json.dumps(payload)
        upload_destinations = []

        # 4) Upload to Foundry
        if not skip_foundry_upload:
            try:
                if not all([foundry_url, api_token, parent_folder_rid]):
                    raise EnvironmentError("Foundry env vars missing.")
                logger.info(f"Uploading '{file_name}' to Foundry...")
                client = FoundryClient(auth=UserTokenAuth(api_token), hostname=foundry_url)
                dataset = client.datasets.Dataset.create(
                    name=file_name.replace(".json", ""),
                    parent_folder_rid=parent_folder_rid
                )
                client.datasets.Dataset.File.upload(
                    dataset_rid=dataset.rid,
                    file_path=file_name,
                    body=content.encode("utf-8"),
                )
                upload_destinations.append("Foundry")
                logger.info(f"Uploaded to Foundry, dataset RID={dataset.rid}")
            except Exception as e:
                logger.error(f"Foundry upload failed: {e}")

        # 5) Upload to Azurite
        try:
            logger.info(f"Uploading '{file_name}' to Azurite container '{azurite_container_name}'...")
            blob_service_client = BlobServiceClient.from_connection_string(azurite_connection_string)
            blob_client = blob_service_client.get_blob_client(container=azurite_container_name, blob=file_name)
            blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
            upload_destinations.append("Azurite Blob Storage")
            logger.info("Uploaded to Azurite.")
        except Exception as e:
            logger.error(f"Azurite upload failed: {e}")

        logger.info(f"Message processing complete for '{file_name}'. Destinations: {upload_destinations}")


def generate_file_name() -> str:
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = uuid4().hex[:8]
    return f"{now}_{suffix}.json"



# import json
# import logging
# import os
# from datetime import datetime
# from uuid import uuid4
# import azure.functions as func
# from azure.storage.blob import BlobServiceClient
# from foundry_sdk import FoundryClient, UserTokenAuth

# logger = logging.getLogger(__name__)


# def main(serviceBusMessage: func.ServiceBusMessage) -> None:
#     logger.info("Foundry file upload function triggered by Service Bus.")

#     try:
#         # Attempt to parse the JSON payload
#         try:
#             message_body = serviceBusMessage.get_body().decode("utf-8")
#             payload = json.loads(message_body)
#         except json.JSONDecodeError as json_error:
#             logger.error("Invalid JSON payload.")
#             raise ValueError("Invalid JSON payload.") from json_error

#         # Validate environment variables
#         foundry_url = os.getenv("FOUNDRY_API_URL")
#         api_token = os.getenv("FOUNDRY_API_TOKEN")
#         parent_folder_rid = os.getenv("FOUNDRY_PARENT_FOLDER_RID")
#         azurite_connection_string = os.getenv("AZURITE_CONNECTION_STRING")
#         azurite_container_name = os.getenv("AZURITE_CONTAINER_NAME")
#         skip_foundry_upload = (
#             os.getenv("SKIP_FOUNDRY_UPLOAD", "false").lower() == "true"
#         )

#         logger.info(f"SKIP_FOUNDRY_UPLOAD is set to: {skip_foundry_upload}")

#         if not azurite_connection_string or not azurite_container_name:
#             raise EnvironmentError("Azurite Blob Storage configuration is missing.")

#         if not isinstance(payload, dict):
#             logger.error("Invalid payload format. Expected a JSON object.")
#             raise ValueError("Invalid payload format. Expected a JSON object.")

#         file_name = generate_file_name()
#         content = json.dumps(payload)
#         upload_destinations = []

#         # Conditionally upload to Foundry
#         if not skip_foundry_upload:
#             try:
#                 if not foundry_url or not api_token or not parent_folder_rid:
#                     raise EnvironmentError(
#                         "Required Foundry environment variables are missing."
#                     )

#                 logger.info(
#                     f"Uploading file '{file_name}' to Foundry (parent folder RID: {parent_folder_rid})..."
#                 )
#                 client = FoundryClient(
#                     auth=UserTokenAuth(api_token), hostname=foundry_url
#                 )

#                 # Create the Foundry dataset before uploading
#                 dataset_name = file_name.replace(".json", "")
#                 dataset = client.datasets.Dataset.create(
#                     name=dataset_name, parent_folder_rid=parent_folder_rid
#                 )

#                 # Upload the file to the Foundry dataset
#                 client.datasets.Dataset.File.upload(
#                     dataset_rid=dataset.rid,
#                     file_path=file_name,
#                     body=content.encode("utf-8"),
#                 )
#                 logger.info(
#                     f"File '{file_name}' uploaded to Foundry successfully. Dataset RID: {dataset.rid}"
#                 )
#                 upload_destinations.append("Foundry")
#             except Exception as foundry_error:
#                 logger.error(f"Failed to upload file to Foundry: {foundry_error}")
#                 raise RuntimeError(
#                     "Failed to upload file to Foundry."
#                 ) from foundry_error

#         else:
#             logger.info("Skipping Foundry upload as per configuration.")

#         # Upload to Azurite Blob Storage
#         try:
#             logger.info(
#                 f"Uploading file '{file_name}' to Azurite Blob Storage container: {azurite_container_name}..."
#             )
#             blob_service_client = BlobServiceClient.from_connection_string(
#                 azurite_connection_string
#             )
#             blob_client = blob_service_client.get_blob_client(
#                 container=azurite_container_name, blob=file_name
#             )

#             # Upload the file to Azurite Blob Storage
#             blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
#             logger.info(
#                 f"File '{file_name}' uploaded to Azurite Blob Storage successfully."
#             )
#             upload_destinations.append("Azurite Blob Storage")
#         except Exception as blob_error:
#             logger.error(f"Failed to upload file to Azurite Blob Storage: {blob_error}")
#             raise RuntimeError(
#                 "Failed to upload file to Azurite Blob Storage."
#             ) from blob_error

#         logger.info(
#             f"File '{file_name}' uploaded successfully to: {', '.join(upload_destinations)}."
#         )
#     except EnvironmentError as env_err:
#         logger.error(f"Environment variables configuration error: {env_err}")
#         raise
#     except Exception as e:
#         logger.error(f"An error occurred: {e}", exc_info=True)
#         raise


# def generate_file_name() -> str:
#     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     unique_suffix = uuid4().hex[:8]
#     return f"{current_time}_{unique_suffix}.json"