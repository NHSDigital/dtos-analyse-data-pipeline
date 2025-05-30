# Use the official Azure Functions Python base image
FROM mcr.microsoft.com/azure-functions/python:4-python3.10

# Set the working directory inside the container
WORKDIR /home/site/wwwroot

# Copy the function app code into the container
COPY . /home/site/wwwroot

# Set environment variable at build time
ARG SUBSCRIPTION_NAME
ENV SUBSCRIPTION_NAME=$SUBSCRIPTION_NAME

# Run the script to update function.json
RUN apt-get update && apt-get install -y python3 && \
    python3 foundry_relay/update_subscription.py

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Azure Functions
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
