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


build-containers: # Build all containers defined in docker-compose.yaml
	@echo "Building all containers using Podman Compose..."
	podman compose build
	@echo "All containers are now built."

standup-containers: # Start all containers defined in docker-compose.yaml
	@echo "Starting all containers using Podman Compose..."
	podman compose up -d
	@echo "All containers are now running."

curl-relay-function: # Send a POST request to the Foundry Relay Function
	@echo "Testing the Foundry Relay Function with curl..."
	curl -X POST http://localhost:7071/api/FoundryRelayFunction \
	-H "Content-Type: application/json" \
	--data @src/FoundryIntegrationService/payload.json
	@echo "Request sent. Check the logs or response for details."

curl-relay-function-100: # Send 100 POST requests to the Foundry Relay Function
	@echo "Sending 100 POST requests to the Foundry Relay Function..."
	for i in {1..100}; do \
				echo "Sending request $$i..."; \
				curl -X POST http://localhost:7071/api/FoundryRelayFunction \
				-H "Content-Type: application/json" \
				--data @src/FoundryIntegrationService/payload.json; \
		done
		@echo "100 requests sent. Check the logs or response for details."

run-unit-tests: # Run all unit tests with pytest
	@echo "Running all unit tests with pytest..."
	# pytest tests/FoundryIntegrationService/test_foundry_relay_function.py
	pytest
	@echo "Unit tests completed."

# ==============================================================================

${VERBOSE}.SILENT: \
	build \
	clean \
	config \
	dependencies \
	deploy \
	build-containers \
	standup-containers \
	curl-relay-function \
	run-unit-tests
