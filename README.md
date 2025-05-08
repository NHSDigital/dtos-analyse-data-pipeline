# Repository Template

[![CI/CD Pull Request](https://github.com/nhs-england-tools/repository-template/actions/workflows/cicd-1-pull-request.yaml/badge.svg)](https://github.com/nhs-england-tools/repository-template/actions/workflows/cicd-1-pull-request.yaml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=repository-template&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=repository-template)

Start with an overview or a brief description of what the project is about and what it does. For example -

Welcome to our repository template designed to streamline your project setup! This robust template provides a reliable starting point for your new projects, covering an essential tech stack and encouraging best practices in documenting.

This repository template aims to foster a user-friendly development environment by ensuring that every included file is concise and adequately self-documented. By adhering to this standard, we can promote increased clarity and maintainability throughout your project's lifecycle. Bundled within this template are resources that pave the way for seamless repository creation. Currently supported technologies are:

- Terraform
- Docker

Make use of this repository template to expedite your project setup and enhance your productivity right from the get-go. Enjoy the advantage of having a well-structured, self-documented project that reduces overhead and increases focus on what truly matters - coding!

## Table of Contents

- [Repository Template](#repository-template)
  - [Table of Contents](#table-of-contents)
  - [Setup](#setup)
    - [Prerequisites](#prerequisites)
    - [Configuration](#configuration)
  - [Usage](#usage)
    - [Testing](#testing)
    - [Azure Service Bus docker emulator](#azure-service-bus-docker-emulator)
  - [Design](#design)
    - [Diagrams](#diagrams)
    - [Modularity](#modularity)
  - [Contributing](#contributing)
  - [Contacts](#contacts)
  - [Licence](#licence)

## Setup

By including preferably a one-liner or if necessary a set of clear CLI instructions we improve user experience. This should be a frictionless installation process that works on various operating systems (macOS, Linux, Windows WSL) and handles all the dependencies.

Clone the repository

```shell
git clone https://github.com/nhs-england-tools/repository-template.git
cd nhs-england-tools/repository-template
```

### Prerequisites

The following software packages, or their equivalents, are expected to be installed and configured:

- [Docker](https://www.docker.com/) container runtime or a compatible tool, e.g. [Podman](https://podman.io/),
- [asdf](https://asdf-vm.com/) version manager,
- [GNU make](https://www.gnu.org/software/make/) 3.82 or later,

> [!NOTE]<br>
> The version of GNU make available by default on macOS is earlier than 3.82. You will need to upgrade it or certain `make` tasks will fail. On macOS, you will need [Homebrew](https://brew.sh/) installed, then to install `make`, like so:
>
> ```shell
> brew install make
> ```
>
> You will then see instructions to fix your [`$PATH`](https://github.com/nhs-england-tools/dotfiles/blob/main/dot_path.tmpl) variable to make the newly installed version available. If you are using [dotfiles](https://github.com/nhs-england-tools/dotfiles), this is all done for you.

- [GNU sed](https://www.gnu.org/software/sed/) and [GNU grep](https://www.gnu.org/software/grep/) are required for the scripted command-line output processing,
- [GNU coreutils](https://www.gnu.org/software/coreutils/) and [GNU binutils](https://www.gnu.org/software/binutils/) may be required to build dependencies like Python, which may need to be compiled during installation,

> [!NOTE]<br>
> For macOS users, installation of the GNU toolchain has been scripted and automated as part of the `dotfiles` project. Please see this [script](https://github.com/nhs-england-tools/dotfiles/blob/main/assets/20-install-base-packages.macos.sh) for details.

- [Python](https://www.python.org/) required to run Git hooks,
- [`jq`](https://jqlang.github.io/jq/) a lightweight and flexible command-line JSON processor.

### Configuration

Installation and configuration of the toolchain dependencies

```shell
make config
```

## Usage

After a successful installation, provide an informative example of how this project can be used. Additional code snippets, screenshots and demos work well in this space. You may also link to the other documentation resources, e.g. the [User Guide](./docs/user-guide.md) to demonstrate more use cases and to show more features.

### Testing

There are `make` tasks for you to configure to run your tests.  Run `make test` to see how they work.  You should be able to use the same entry points for local development as in your CI pipeline.

### Azure Service Bus docker emulator

There is a requirement to allow us to be able to test out the analyse data pipeline locally. To do this we have created an Azure Service bus emulator. To test this out you will have to run: -

```shell
podman-compose -f docker-compose.yaml up -d
```

This should bring up two services, both `sqledge` and `servicebus-emulator`: -

```shell
% podman ps
CONTAINER ID  IMAGE                                                         COMMAND               CREATED      STATUS      PORTS                                                     NAMES
e4c9e73d3610  mcr.microsoft.com/mssql/server:2022-latest                    /opt/mssql/bin/sq...  4 hours ago  Up 4 hours  1433/tcp                                                  sqledge
7226f76cd694  mcr.microsoft.com/azure-messaging/servicebus-emulator:latest                        4 hours ago  Up 4 hours  0.0.0.0:5300->5300/tcp, 0.0.0.0:5672->5672/tcp, 8080/tcp  servicebus-emulator
```

If the components have been successfully deployed, you can test the setup using two Python scripts located in the scripts/docker directory:
service-bus-producer.py: Sends a message to queue.1 on the Azure Service Bus emulator.
service-bus-consumer.py: Listens for and receives messages from queue.1.

Run the producer script
This sends a test message to the queue.

```shell
(venv) % python3 scripts/docker/service-bus-producer.py
Message sent.
(venv) %
```

Run the consumer script
This will pick up and display the message.

```shell
(venv) % python3 scripts/docker/service-bus-consumer.py
Listening for messages...
Received: Hello from local sender!
```

Please note that it might be necessary to purge the docker images between starting and stopping `podman-compose`. This can be achieved via doing commands:-

```shell
(venv) % podman-compose -f docker-compose.yaml down
servicebus-emulator
sqledge
servicebus-emulator
sqledge
af571ddd5671ac646e503ccea11b8fde16edc7ad65a918e7af1d7d4a29d4d434
microsoft-azure-servicebus-emulator_sb-emulator
(venv) %
```

Then find the image IDs which need to be removed: -

```shell
(venv) % podman images
REPOSITORY                                             TAG          IMAGE ID      CREATED       SIZE
mcr.microsoft.com/azure-messaging/servicebus-emulator  latest       77e64bec8af0  8 weeks ago   225 MB
mcr.microsoft.com/mssql/server                         2022-latest  2b41d0be8283  2 months ago  1.66 GB
```

Then remove the images using command `podman image rm <IMAGE ID>`

```shell
(venv) % podman image rm 77e64bec8af0 2b41d0be8283
Untagged: mcr.microsoft.com/azure-messaging/servicebus-emulator:latest
Untagged: mcr.microsoft.com/mssql/server:2022-latest
Deleted: 77e64bec8af06eee8ba4952311cd16b9e360b8da1d3a9f501191ac1ba4f11f74
Deleted: 2b41d0be82839692f678a709e8b7dd6106ee4776b0e70759c59b067730058b04

```

## Design

### Diagrams

The [C4 model](https://c4model.com/) is a simple and intuitive way to create software architecture diagrams that are clear, consistent, scalable and most importantly collaborative. This should result in documenting all the system interfaces, external dependencies and integration points.

![Repository Template](./docs/diagrams/Repository_Template_GitHub_Generic.png)

The source for diagrams should be in Git for change control and review purposes. Recommendations are [draw.io](https://app.diagrams.net/) (example above in [docs](.docs/diagrams/) folder) and [Mermaids](https://github.com/mermaid-js/mermaid). Here is an example Mermaids sequence diagram:

```mermaid
sequenceDiagram
    User->>+Service: GET /users?params=...
    Service->>Service: auth request
    Service->>Database: get all users
    Database-->>Service: list of users
    Service->>Service: filter users
    Service-->>-User: list[User]
```

### Modularity

Most of the projects are built with customisability and extendability in mind. At a minimum, this can be achieved by implementing service level configuration options and settings. The intention of this section is to show how this can be used. If the system processes data, you could mention here for example how the input is prepared for testing - anonymised, synthetic or live data.

## Contributing

Describe or link templates on how to raise an issue, feature request or make a contribution to the codebase. Reference the other documentation files, like

- Environment setup for contribution, i.e. `CONTRIBUTING.md`
- Coding standards, branching, linting, practices for development and testing
- Release process, versioning, changelog
- Backlog, board, roadmap, ways of working
- High-level requirements, guiding principles, decision records, etc.

## Contacts

Provide a way to contact the owners of this project. It can be a team, an individual or information on the means of getting in touch via active communication channels, e.g. opening a GitHub discussion, raising an issue, etc.

## Licence

> The [LICENCE.md](./LICENCE.md) file will need to be updated with the correct year and owner

Unless stated otherwise, the codebase is released under the MIT License. This covers both the codebase and any sample code in the documentation.

Any HTML or Markdown documentation is [© Crown Copyright](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/) and available under the terms of the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
