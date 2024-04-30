#!/usr/bin/env bash
# Install psql, docker, and docker-compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose postgresql-client-common postgresql-client
# This is to run the docker compose with both the PostgREST server and the PostgreSQL database containers.
sudo docker-compose -f docker_compose_yml/docker-compose.dev.yml down
sudo nohup docker-compose -f docker_compose_yml/docker-compose.dev.yml up >database.dev.out 2>database.dev.err & #TODO Have the logs at the right place