#!/usr/bin/env bash

# Install psql, docker, and docker-compose
apt-get update --quiet
apt-get install -y docker.io docker-compose postgresql-client-common postgresql-client --quiet

# This is to compile the Docker image of the PostgreSQL database with init_database.sql as entrypoint function.
GIT_REPO_NAME='nrt_production_system'
ROOT_FOLDER=$(python3 -c "import sys;import os;ROOT_FOLDER = '/'.join(os.getcwd().split('$GIT_REPO_NAME')[:-1]);\
                          assert(ROOT_FOLDER != ''), 'Please move to the $GIT_REPO_NAME Git folder...';\
                          print(f'{ROOT_FOLDER}'+'$GIT_REPO_NAME');")

cd $ROOT_FOLDER/HRWSI_database
docker build -t hrwsi-database-prod:latest .

# This is to run the docker compose with both the PostgREST server and the PostgreSQL database containers.
cd $ROOT_FOLDER/HRWSI_database/docker_compose_yml
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d