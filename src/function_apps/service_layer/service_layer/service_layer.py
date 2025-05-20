import json
import logging
import os
from datetime import datetime
from http import HTTPStatus
from uuid import uuid4
import azure.functions as func
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Service Bus file upload function triggered.")

    try:
        # Attempt to parse the JSON payload
        try:
            payload = req.get_json()
        except json.JSONDecodeError:
            return func.HttpResponse(
                "Invalid JSON payload.", status_code=HTTPStatus.BAD_REQUEST
            )

        # Validate environment variables
        connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
        queue_name = os.getenv("QUEUE_NAME")

        if not connection_str:
            raise EnvironmentError("Azure Service Bus connection string is missing.")

        if not isinstance(payload, dict):
            return func.HttpResponse(
                "Invalid payload format. Expected a JSON object.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            client = ServiceBusClient.from_connection_string(connection_str)
            with client:
                sender = client.get_queue_sender(queue_name=queue_name)
                with sender:
                    try:
                        json_message = json.dumps(payload)
                        print(json_message)
                        message = ServiceBusMessage(json_message)
                        sender.send_messages(message)
                        # Return success response
                        return func.HttpResponse(
                            f"Payload uploaded successfully to service bus emulator. ",
                            status_code=HTTPStatus.OK,
                        )

                    except ServiceBusError as e:
                        print(f"ServiceBusError occurred while produce a message: {e}")

        except ServiceBusError as e:
            print(f"ServiceBusError occurred when connecting to Service Bus: {e}")

    # Handle exceptions
    except EnvironmentError as env_err:
        logger.error(f"Environment variables configuration error: {env_err}")
        return func.HttpResponse(str(env_err), status_code=HTTPStatus.BAD_REQUEST)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return func.HttpResponse(
            "An internal server error occurred.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
