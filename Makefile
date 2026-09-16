.PHONY: help build build-amd64 up down logs ps clean install-cplex

help:
	@echo "Planar System Deployment Commands:"
	@echo "  make build         - Build container images natively on the current machine"
	@echo "  make build-amd64   - Cross-compile container images targeting linux/amd64 with Buildx"
	@echo "  make install-cplex - Silently install CPLEX Studio into the persistent cplex volume"
	@echo "  make up            - Start the entire stack in detached mode"
	@echo "  make down          - Stop and remove the running containers and network"
	@echo "  make logs          - Follow live aggregated container logs"
	@echo "  make ps            - Check container status and healthchecks"
	@echo "  make clean         - Stop containers and remove persistent volumes"

# Native build on host (e.g. directly on remote x86_64 Linux or local Mac)
build:
	docker compose build

# Cross-compilation for deployment to remote x86_64 Linux servers
build-amd64:
	DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose build

# Install IBM CPLEX Studio into persistent Docker volume
install-cplex:
	docker compose --profile setup run --rm cplex_installer

# Start services in the background
up:
	docker compose up -d

# Stop services
down:
	docker compose down

# Follow logs
logs:
	docker compose logs -f

# Check health and status
ps:
	docker compose ps

# Remove volumes (WARNING: wipes database and cache data)
clean:
	docker compose down -v
