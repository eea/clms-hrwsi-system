#!/usr/bin/env bash
# Install psql, docker, and docker-compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose postgresql-client-common postgresql-client
# This is to run the docker compose with both the PostgREST server and the PostgreSQL database containers.
sudo docker-compose -f docker-compose.prod.yml down
sudo nohup docker-compose -f docker-compose.prod.yml up >database.prod.out 2>database.prod.err & #TODO Have the logs at the right place