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

## Troubleshooting

- If postgres is not initialised correctly, remove the postgres container and run `make` (or `docker compose`) again.
  For more, see [here](https://hub.docker.com/_/postgres#:~:text=starting%20the%20service.-,Warning,-%3A%20scripts%20in%20/docker).
