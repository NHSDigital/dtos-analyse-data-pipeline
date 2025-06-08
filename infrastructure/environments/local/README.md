# Local development

## Overview

We use docker compose to emulate our pipeline from BSSelect to FDP, locally.

The pipeline diagram is FIXME - (we can do this on another ticket).

The pipeline allows us to test how CRUD operations in BSSelect cause events to be emitted.
BSSelect pushes these events to NSP for processing, and they ultimately end up in FDP.

The process is as follows...
TODO - describe the process in a few sentences.
See [mural link](https://app.mural.co/t/nhsdigital8118/m/nhsdigital8118/1739874458977/c97dae9bbdd1a06d2abb16863a70f8b783acfc36?wid=0-1746632950738) for inspiration.

### Postgres

To test event emission in postgres:

- Go to the project root.
- Start the database: `make local-environment action=start`
- Connect to the database: `psql -h localhost -U test-user -d test-db`
- LISTEN for changes to the subjects table: `LISTEN subjects;`
- Run CRUD operations to cause notification events:

```sql
INSERT INTO subjects (name, age) VALUES ('Kate', 40);
INSERT INTO subjects (name, age) VALUES ('Elizabeth', 35);
UPDATE subjects SET age=99 WHERE ID = 1;
DELETE FROM subjects WHERE ID = 1;
```

## Interactive development

TLDR - Make sure no containers are running. Start VSCode. Run the command `Dev Containers: Reopen in Container`. Chose the container you want.

### Overview

We use VSCode [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) for interactive local development.
Specifically, the [Connect to multiple containers](http://code.visualstudio.com/remote/advancedcontainers/connect-multiple-containers) option.
The VScode command `Dev Containers: Add Dev Container Configuration Files...` gives a starter config for each container.
For more config documentation, see: [json reference](https://containers.dev/implementors/json_reference/).
In principle, this lets you connect to any container in the [docker-compose](../../../docker-compose.yaml) stack.
In practice, we only setup connections to the containers we want to develop in:

- [bsselect-event-poster](../../../.devcontainer/bsselect-event-poster)
- [service-layer](../../../.devcontainer/service-layer)

### Setting things up

The first time you enter a container, install @recommented VSCode extensions.

### Troubleshooting

- General fixes:
  - Cleaning up containers. E.g. `docker rm --all --force`
  - Checking container logs. E.g. `docker logs -f bsselect-db`

- 'Workspace does not exist'
  - Run `docker compose down` to avoid VSCode getting confused about duplicate containers.

## Troubleshooting

- If postgres is not initialised correctly, remove the postgres container and run `make` (or `docker compose`) again.
  For more, see [official image docs](https://hub.docker.com/_/postgres#:~:text=starting%20the%20service.-,Warning,-%3A%20scripts%20in%20/docker).
