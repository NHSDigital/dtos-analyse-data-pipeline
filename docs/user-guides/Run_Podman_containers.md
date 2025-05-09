# Running Containers Guide

This guide explains how to start, stop, restart, and manage containers in your environment for macOS users.

## Setting Up the .env File

Before starting the containers, create a `.env` file based on the provided `env.template` file.

1. **Locate the Template**
   The `env.template` file contains placeholders for environment variables.

2. **Create the .env File**
   Copy the `env.template` file to `.env`:

   ```bash
   cp env.template .env
   ```

3. **Configure the .env File**
   Open the `.env` file and set the required values. For example:

   ```env
   # Azure storage container settings
   AZURITE_CONNECTION_STRING="YourAzuriteConnectionString"
   AZURITE_CONTAINER_NAME="inbound"
   AZURITE_POISON_CONTAINER_NAME="inbound-poison"

   # Foundry API settings
   FOUNDRY_RESOURCE_ID="YourFoundryResourceID"
   FOUNDRY_API_URL="YourFoundryAPIURL"
   FOUNDRY_API_TOKEN="YourFoundryAPIToken"

   # Docker network settings
   DOCKER_NETWORK_TYPE=bridge  # macOS users
   # DOCKER_NETWORK_TYPE=host  # Windows users
   ```

   Ensure all required values are filled in based on your environment.

## Starting Containers

You can start containers manually with Podman Compose commands.

1. **Start Azurite**
   Start Azurite and its setup service:

   ```bash
   podman compose up -d azurite
   podman compose up -d azurite-setup
   ```

2. **Start Remaining Services**
   Once Azurite is running, start the remaining services:

   ```bash
   podman compose up -d
   ```

## Stopping Containers

- **Stop All Containers**:

  ```bash
  podman compose down
  ```

- **Stop a Specific Container**:

  ```bash
  podman compose down foundry-relay-function
  ```

## Rebuilding Containers

If you make changes to the code, rebuild the container image:

- **Rebuild a Specific Service**:

  ```bash
  podman compose build foundry-relay-function
  ```

## Restarting Containers

- **Restart All Containers**:

  ```bash
  podman compose restart
  ```

- **Restart with Stop and Start**:

  ```bash
  podman compose down && podman compose up -d
  ```
