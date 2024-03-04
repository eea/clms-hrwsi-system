# Launchers

We developped two different launchers to be used as utils to run or shut-down DB Docker containers in different contexts.

## [init_dev_database.sh](init_dev_database.sh)

It is to be used to prepare and launch a DB using [docker-compose.dev.yml](../docker_compose_yml/docker-compose.dev.yml). It installs the required third-party softwares, closes an eventual previous local instance of the database, runs a new one and checks wether the tests passed using [hrwsi_result_test_checker.sh](../test_utils/hrwsi_result_test_checker.sh).

## [init_prod_database.sh](init_prod_database.sh)

It is to be used to prepare and launch a DB using [docker-compose.prod.yml](../docker_compose_yml/docker-compose.prod.yml). It installs the required third-party softwares, closes an eventual previous local instance of the database, and runs a new one.

## [terminate_dev_database.sh](terminate_dev_database.sh)

Calls `docker-compose down` on [docker-compose.dev.yml](../docker_compose_yml/docker-compose.dev.yml).
> This MUST NOT BE USED on production as it erases the content of the database.