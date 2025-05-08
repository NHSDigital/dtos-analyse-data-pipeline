import os
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage

load_dotenv()

connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
if not connection_str:
    raise ValueError("Missing SERVICE_BUS_CONNECTION_STR in .env file")
client = ServiceBusClient.from_connection_string(connection_str)

try:
    with client:
        sender = client.get_queue_sender(queue_name="queue.1")
        with sender:
            try:
                message = ServiceBusMessage("Hello from local sender!")
                sender.send_messages(message)
                print("Message sent.")

            except ServiceBusError as e:
                print(f"ServiceBusError occurred while produce a message: {e}")


except ServiceBusError as e:
    print(f"ServiceBusError occurred when connecting to Service Bus: {e}")
