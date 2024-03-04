#!/usr/bin/env bash

# Close and entirely delete the database docker containers
# DO NOT USE OR ADAPT FOR PRODUCTION
GIT_REPO_NAME='nrt_production_system'
ROOT_FOLDER=$(python3 -c "import sys;import os;ROOT_FOLDER = '/'.join(os.getcwd().split('$GIT_REPO_NAME')[:-1]);\
                          assert(ROOT_FOLDER != ''), 'Please move to the $GIT_REPO_NAME Git folder...';\
                          print(f'{ROOT_FOLDER}'+'$GIT_REPO_NAME');")

cd $ROOT_FOLDER/HRWSI_database
docker-compose -f docker_compose_yml/docker-compose.dev.yml down
