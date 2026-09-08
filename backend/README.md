# Xplanar Experiment Configurator

This projects includes backend implementation for Xplanar Experiment Configurator.

## Contacts
**Author:** Vojtěch Mička  
**Email:** mickavo2@student.cvut.cz 

## Content

This repository contains the following directories and packages: 
- `alembic` - directory with configuration and database migration scripts for Alembic
- `api` - package related to the presentation layer
- `clients` - package related to the asynchronous task processing
- `core` - package with configuration files
- `db` - package related to the database layer
- `docker-int` - directory with SQL script to set up database for tests
- `domain` - package related to the domain layer
- `mappers` - package with mapping functions
- `services` - package with services from application layer
- `solvers` - package with integrated optimization models
- `templates` - directory with template for Gantt chart generation
- `tests` - package related to tests

## Configuration

- Configuration files can be found in the core package.
- Main app settings can be found in `core/config.py`,
and they can be modified via environment variables.

## Dependencies

- Project dependencies can be found in `requirements.txt`.

## Solvers

- To be able to run any experiments it's necessary to have Gurobi Optimizer and at least one of other solvers installed.
- All solvers require valid licence. Currently, it's possible to run one experiment at a time, therefore personal licence for one concurrent usage is enough.
- **Gurobi Optimizer** - solver for routing phase used in combination with all models
- **Hexaly Optimizer** - solver for medicine
- **IBM CPLEX CP Optimizer** - solver for medicine and perfume

## Database Configuration

There's one docker compose file for both databases (PostgreSQL and Redis).

### How to Start Databases

```
docker-compose up -d
```

### How to Create Initial PostgreSQL Migration

```
alembic revision --autogenerate -m "Initial migration"
```

### How to Apply PostgreSQL Migration

```
alembic upgrade head
```

## API

### Where to Find Swagger API Documentation

Open the following link in your browser when app is running: <http://127.0.0.1:8000/docs>

## Tests

- Unit tests can be run any time.
- Integration tests for repositories need PostgreSQL database which can be started via docker compose file.

### How to Run Tests

```
pytest
```

### How to Generate Documentation

- It's possible to generate project documentation automatically via pdoc command.
- Generated documentation can be found in docs directory and it can be opened via browser.

```
pdoc . !.venv !alembic !data !docker-init !templates !tests -o ./docs
```

## How to Run App

- Backend is divided into three parts.
- It's possible to start only databases and API. In that way it's possible to use the app. It's possible to create experiments, but they won't run.
- To be able to run experiments it's necessary to start Celery worker.

### Start Databases

```
docker compose up -d
```

**IMPORTANT:** If this is your first time running the database, you must apply the database migrations to create the required tables:

```
alembic upgrade head
```

### Start API

```
python main.py
```

### Start Celery Worker

```
celery -A core.celery_app worker --loglevel=info -P solo
```

## License

[MIT license](LICENSE)