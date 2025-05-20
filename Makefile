# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed locally and in the CD pipeline.

include scripts/init.mk

# ==============================================================================

# Example CI/CD targets are: dependencies, build, publish, deploy, clean, etc.

dependencies: # Install dependencies needed to build and test the project @Pipeline
	# TODO: Implement installation of your project dependencies

build: # Build the project artefact @Pipeline
	# TODO: Implement the artefact build step

publish: # Publish the project artefact @Pipeline
	# TODO: Implement the artefact publishing step

deploy: # Deploy the project artefact to the target environment @Pipeline
	# TODO: Implement the artefact deployment step

clean:: # Clean-up project resources (main) @Operations
	# TODO: Implement project resources clean-up step

config:: # Configure development environment (main) @Configuration
	# TODO: Use only 'make' targets that are specific to this project, e.g. you may not need to install Node.js
	make _install-dependencies

# ==============================================================================

# Custom targets for local development and testing

install-dependencies: # Install dependencies needed to build and test the project
	@echo "Installing dependencies..."
	@echo "Installing Python dependencies..."
	pip install -r src/FoundryIntegrationService/requirements.txt
	@echo "All project dependencies are installed."

build-local-containers: # Build all containers defined in docker-compose.yaml
	@echo "Building all containers..."
	docker compose build
	@echo "All containers are now built."

standup-local-containers: # Start all containers defined in docker-compose.yaml
	@echo "Starting all containers..."
	docker compose up -d
	@echo "All containers are now running."

stop-local-containers: # Stop all containers defined in docker-compose.yaml
	@echo "Stopping all containers..."
	docker compose down
	@echo "All containers are now stopped."

remove-container-images: # Remove all container images
	@echo "Removing all container images..."
	docker rmi -a -f
	@echo "All container images have been removed."

prune-unused-images: # Prune all unused container images
		@echo "Pruning all unused container images..."
		docker image prune -a -f
		@echo "All unused container images have been pruned."

curl-relay-function: # Send a POST request to the Foundry Relay Function
	@echo "Testing the Foundry Relay Function with curl..."
	curl -X POST http://localhost:7071/api/FoundryRelayFunction \
	-H "Content-Type: application/json" \
	--data @src/function_apps/FoundryIntegrationService/payload.json
	@echo "Request sent. Check the logs or response for details."

curl-service-layer-function: # Send a POST request to the Service Layer Function
	@echo "Testing the Foundry Relay Function with curl..."
	curl -X POST http://localhost:7072/api/service_layer \
	-H "Content-Type: application/json" \
	--data @src/function_apps/FoundryIntegrationService/payload.json
	@echo "Request sent. Check the logs or response for details."

run-unit-tests: # Run all unit tests with pytest
	@echo "Running all unit tests with pytest..."
	# pytest tests/FoundryIntegrationService/test_foundry_relay_function.py
	pytest
	@echo "Unit tests completed."

local-pipeline-end-to-end-fdp: # Run a local Azure Function App with containers and test it
	@echo "Starting the local Azure Function App pipeline end to end..."
	@echo "Step 1: Standing up all containers..."
	make standup-local-containers
	@echo "Step 2: Inserting sample subjects into the database..."
	make insert-sample-subjects
	@echo "Local pipeline execution completed."

write-service-bus-emulator: # Write to the Service Bus Emulator
	@echo "Writing to the Service Bus Emulator..."
	python scripts/docker/service-bus-producer.py
	@echo "Wrote to Service Bus Emulator."

read-service-bus-emulator: # Read from the Service Bus Emulator
	@echo "Reading from the Service Bus Emulator..."
	python scripts/docker/service-bus-consumer.py
	@echo "Read from Service Bus Emulator."

write-service-bus-emulator-payload: # Write payload messages to the Service Bus Emulator
	@echo "Writing payload to the Service Bus Emulator..."
	python scripts/docker/service-bus-producer-payload.py
	@echo "Wrote payload to Service Bus Emulator."

insert-sample-data: # Insert sample data into the database to trigger the pipeline
	@echo "Inserting sample data into the database using script..."
	set -o allexport; source .env; set +o allexport; ./insert_sample_data.sh
	@echo "Sample data inserted."


# ==============================================================================

# Local development

# TODO - tidy this when integrating with others in https://nhsd-jira.digital.nhs.uk/browse/DTOSS-8699
action ?= start
local-environment: # Local containerised development environment: action=[start, stop, default is 'start'] @Development
	if [ "$(action)" = "start" ]; then \
			echo "Starting local environment..."; \
			docker compose -f infrastructure/environments/local/docker-compose.yaml up -d --build; \
	elif [ "$(action)" = "stop" ]; then \
			echo "Stopping local environment..."; \
			docker compose -f infrastructure/environments/local/docker-compose.yaml down; \
	else \
			echo "Unknown action: '$(action)'. Use 'start' or 'stop'."; \
			exit 1; \
	fi

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \
	local-environment
