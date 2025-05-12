import os
import time
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError

load_dotenv()

connection_str = os.getenv("SERVICE_BUS_CONNECTION_STR")
if not connection_str:
    raise ValueError("Missing SERVICE_BUS_CONNECTION_STR in .env file")

client = ServiceBusClient.from_connection_string(connection_str)

try:
    with client:
        receiver = client.get_queue_receiver(queue_name="queue.1", max_wait_time=5)
        with receiver:
            print("Listening for messages...")
            while True:
                try:
                    messages = receiver.receive_messages(max_message_count=10)
                    if not messages:
                        time.sleep(1)
                        continue

                    for msg in messages:
                        print("Received:", str(msg))
                        receiver.complete_message(msg)

                except ServiceBusError as e:
                    print(f"ServiceBusError occurred while receiving or completing messages: {e}")
                    time.sleep(5)  # backoff before retrying

except ServiceBusError as e:
    print(f"ServiceBusError occurred when connecting to Service Bus: {e}")

