# Local development

## Overview

TODO - as part of end-to-end run [ticket](https://nhsd-jira.digital.nhs.uk/browse/DTOSS-8699)

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
