# Functional Tests with pytest-bdd

This project uses [pytest-bdd](https://pytest-bdd.readthedocs.io/) for behavior-driven development (BDD) style functional testing.

## Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-bdd](https://pytest-bdd.readthedocs.io/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [azure-storage-blob](https://pypi.org/project/azure-storage-blob/)

Install dependencies:

```sh
pip install -r requirements.txt
```

## Environment Setup

1. Copy `.env.template` to `.env` in the project root and fill in the required values, e.g.:
    ```
    AZURITE_CONNECTION_STRING=your-azurite-connection-string
    ```

2. Ensure any required services (e.g., Azurite, API, etc.) are running.
   You can use Podman or Docker Compose:
   ```sh
   podman compose -f docker-compose.yaml up -d
   # or
   docker compose -f docker-compose.yaml up -d
   ```

## Running the Tests

From the project root, run:

```sh
pytest tests/functionaltests
```

To see print output in real time, use:

```sh
pytest -s tests/functionaltests
```

## Generating Reports

- **HTML Report** (requires `pytest-html`):
  ```sh
  pip install pytest-html
  pytest --html=report.html
  ```

- **JUnit XML Report** (for CI/CD):
  ```sh
  pytest --junitxml=report.xml
  ```

## Directory Structure

```
tests/
  functionaltests/
    features/
      EndToEndSmokeTest.feature
    payloads/
      sample_payload.json
    test_end_to_end_smoke.py
```

## Writing Scenarios

Feature files are written in Gherkin syntax and placed in the `features/` directory.
Step definitions are implemented in Python test files.

---

For more details, see the [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/).
