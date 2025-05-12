import os
import json
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage

# Load environment variables
load_dotenv()

# Get the Service Bus connection string from the environment
connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
if not connection_str:
    raise ValueError("Missing SERVICE_BUS_CONNECTION_STR in .env file")

# Path to the payload.json file
payload_file = "src/FoundryIntegrationService/payload.json"

# Read the payload from the JSON file
if not os.path.exists(payload_file):
    raise FileNotFoundError(f"Payload file '{payload_file}' not found.")

with open(payload_file, "r") as file:
    payload = json.load(file)

# Convert the payload to a JSON string
message_body = json.dumps(payload)

# Create a Service Bus client
client = ServiceBusClient.from_connection_string(connection_str)

# Send the message to the queue
with client:
    sender = client.get_queue_sender(queue_name="queue.1")
    with sender:
        message = ServiceBusMessage(message_body)
        sender.send_messages(message)
        print(f"Message sent: {message_body}")
