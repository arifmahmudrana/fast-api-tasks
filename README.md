# FastAPI Tasks API with User System with OAuth2, MySQL, Docker, and Testing

## Features
- [x] FastAPI app with OAuth2 authentication
- [x] MySQL database via SQLAlchemy
- [x] Alembic for migrations
- [x] Environment variables managed by python-dotenv
- [x] Local development with Docker Compose and hot reloading
- [x] Unit, integration, and end-to-end tests
- [ ] Tasks management using MongoDB
- [ ] User profile image using AWS S3
- [ ] Caching
- [ ] ELK application log
- [ ] CI/CD
- [ ] User password reset
- [ ] Tasks search using elastic search
- [ ] Kibana dashboard
- [ ] Queue/celery for elastic indexing for tasks
- [ ] Deployment
- [ ] Kubernetes deployment to GCP
- [ ] Monitoring using Prometheus and Grafana
- [ ] Stress testing using k6
- [ ] Benchmarking


## Getting Started

### 1. Environment Setup
- Python 3.11+
- Create a virtual environment: `python3 -m venv .venv`
- Activate it: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### 2. Local Development
- Copy `.env.example` to `.env` and update values as needed.
- Start services: `docker-compose up --build`
- App runs at http://localhost:8000
- MySQL runs at localhost:3306

#### Running the app without Docker Compose
- Ensure your MySQL server is running and matches the credentials in your `.env` file.
- Activate your virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run the app with hot reload:
  ```sh
  uvicorn app.main:app --reload
  ```
- The app will be available at http://localhost:8000

### 3. Database Migrations
- Run migrations: `PYTHONPATH=. alembic upgrade head`  
- Create migrations: `PYTHONPATH=. alembic revision --autogenerate -m 'MESSAGE'`  
Adding `PYTHONPATH=.` ensures the `app` module is found

### 4. Testing
- Run all tests: `pytest`
- Or use the Makefile for full test automation (including MySQL in Docker):
  ```sh
  make test
  ```

## Makefile Usage

The Makefile provides convenient commands for development and testing:

- `make venv` — Create and install dependencies in a virtual environment
- `make run` — Run the FastAPI app locally with hot reload
- `make up` — Start the app and MySQL using Docker Compose
- `make down` — Stop and remove Docker Compose containers
- `make migrate` — Run Alembic migrations
- `make test` — Spin up a MySQL Docker container, run tests, and clean up
- `make coverage` — Run tests with coverage and generate an HTML report in `htmlcov/`
- `make docker-clean` — Remove all Docker containers and volumes

### Requirements
- [Make](https://www.gnu.org/software/make/) (install via `brew install make` on macOS or your package manager)
- Docker and Docker Compose (for Docker-based commands)

To run tests with MySQL in Docker:
```sh
make test
```
To run the app locally (without Docker):
```sh
make venv
make run
```

## Project Structure
- `app/` - FastAPI application code
- `tests/` - All test code
- `alembic/` - Alembic migrations

## Useful Commands
- `docker-compose up --build` - Start app and DB
- `alembic revision --autogenerate -m "message"` - Create migration
- `alembic upgrade head` - Apply migrations
- `pytest` - Run tests

---

For more details, see each folder's README or docstrings.
