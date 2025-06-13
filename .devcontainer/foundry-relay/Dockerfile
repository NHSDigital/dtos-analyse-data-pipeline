# Use the official Azure Functions Python base image
FROM mcr.microsoft.com/azure-functions/python:4-python3.10

# This block is needed for local, devcontainers development.
# The base image doesn't contain git or azure-functions-core-tools.
# Source: https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=linux%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python#install-the-azure-functions-core-tools
RUN apt-get install -y git lsb-release
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
RUN mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
RUN sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/debian/$(lsb_release -rs 2>/dev/null | cut -d'.' -f 1)/prod $(lsb_release -cs 2>/dev/null) main" > /etc/apt/sources.list.d/dotnetdev.list'
RUN apt-get update
RUN apt-get install azure-functions-core-tools-4

# Set the working directory inside the container
WORKDIR /home/site/wwwroot

# Copy the function app code into the container
COPY ../../src/function_apps/foundry_relay/ /home/site/wwwroot

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Azure Functions
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
