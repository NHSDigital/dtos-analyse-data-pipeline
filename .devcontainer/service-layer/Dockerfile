# Use the official Azure Functions Python base image
FROM mcr.microsoft.com/azure-functions/python:4-python3.10

# Set the working directory inside the container
WORKDIR /home/site/wwwroot

COPY .devcontainer/function-app-setup.sh /function-app-setup.sh
RUN sh /function-app-setup.sh

# Copy the function app code into the container
COPY ../../src/function_apps/service_layer/ /home/site/wwwroot

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Azure Functions
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
