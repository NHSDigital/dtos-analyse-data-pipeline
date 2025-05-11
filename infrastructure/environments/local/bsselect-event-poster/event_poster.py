import psycopg2
import psycopg2.extensions
import json
import os
import requests
import select
from dotenv import load_dotenv

load_dotenv()

NSP_URL = "http://host.docker.internal:8080" # os.environ.get("NSP_SERVICE_LAYER_URL")

# Connect to your database
conn = psycopg2.connect(
    dbname=os.environ.get("POSTGRES_DB"),
    user=os.environ.get("POSTGRES_USER"),
    password=os.environ.get("POSTGRES_PASSWORD"),
    host=os.environ.get("POSTGRES_HOST"),
    port=os.environ.get("POSTGRES_PORT"),
)



# Set isolation level to autocommit
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

# Create cursor and listen for notifications
cursor = conn.cursor()
cursor.execute("LISTEN subjects;")

print("Listening for notifications...")
while True:
    # conn.poll() didn't work without this blocking call
    if select.select([conn], [], [], 5) == ([], [], []):
        # Timeout, no notifications
        print("Timeout")
        continue

    print("Ooh, there's something to poll!")
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        # Parse the JSON payload and pretty print it
        data = json.loads(notify.payload)
        print(json.dumps(data, indent=2))


        result = requests.post(NSP_URL, json = notify.payload)

        print('result is ', result)
