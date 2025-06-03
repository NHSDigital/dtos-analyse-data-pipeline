import json
import logging
import os
from http import HTTPStatus
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Service Bus file upload function triggered.")

    try:
        # Parse the incoming JSON payload
        try:
            payload = req.get_json()
        except json.JSONDecodeError:
            return func.HttpResponse("Invalid JSON payload.", status_code=HTTPStatus.BAD_REQUEST)

        if not isinstance(payload, dict):
            return func.HttpResponse("Invalid payload format. Expected a JSON object.", status_code=HTTPStatus.BAD_REQUEST)

        topic_name = os.getenv("TOPIC_NAME")

        if not topic_name:
            raise EnvironmentError("Service Bus topic name is missing.")

        # Create ServiceBusClient
        if use_managed_identity:
            logger.info("Connecting to the Service Bus via Managed Identity.")

            fully_qualified_namespace = os.getenv("SERVICE_BUS_NAMESPACE")
            if not fully_qualified_namespace:
                raise EnvironmentError("SERVICE_BUS_NAMESPACE is required when using managed identity.")
            logger.info("Using Managed Identity for Service Bus authentication.")
            credential = DefaultAzureCredential()
            client = ServiceBusClient(fully_qualified_namespace=fully_qualified_namespace, credential=credential)
        else:
            # Validate environment variables
            logger.info("Connecting to the Service Bus via a connection string.")
            connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
            if not connection_str:
                raise EnvironmentError("SERVICE_BUS_CONNECTION_STR is required when not using managed identity.")
            logger.info("Using connection string for Service Bus authentication.")
            client = ServiceBusClient.from_connection_string(connection_str)

        # Send message to topic
        with client:
            sender = client.get_topic_sender(topic_name=topic_name)
            with sender:
                json_message = json.dumps(payload)
                message = ServiceBusMessage(json_message)
                sender.send_messages(message)
                return func.HttpResponse("Payload uploaded successfully to Service Bus.", status_code=HTTPStatus.OK)

    except EnvironmentError as env_err:
        logger.error(f"Configuration error: {env_err}")
        return func.HttpResponse(str(env_err), status_code=HTTPStatus.BAD_REQUEST)
    except ServiceBusError as sb_err:
        logger.error(f"Service Bus error: {sb_err}")
        return func.HttpResponse(f"Service Bus error: {sb_err}", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return func.HttpResponse("An internal server error occurred.", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
