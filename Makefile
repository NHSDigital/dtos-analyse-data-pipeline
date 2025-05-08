# This file is for you! Edit it to implement your own hooks (make targets) into
# the project as automated steps to be executed on locally and in the CD pipeline.

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

# Local development targets

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
