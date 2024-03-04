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
docker build -t hrwsi-database-dev:latest .

# This is to run the docker compose with both the PostgREST server and the PostgreSQL database containers.
cd $ROOT_FOLDER/HRWSI_database/docker_compose_yml
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Checking for the tests results
sleep 15
cd $ROOT_FOLDER/HRWSI_database
docker cp hrwsi_database_container:/home/hrwsi_db_tests.log .
cat hrwsi_db_tests.log
last_line=$(tail hrwsi_db_tests.log -n 1)
last_four_characters=${last_line:(-4)}
cd $ROOT_FOLDER/HRWSI_database/test_utils
./hrwsi_result_test_checker.sh $last_four_characters