# Init Database

This section explains how the database schema is separated in several files.

## SQL files names

The SQL files describing the HRWSI database schema follow this naming convention: {priority_order}_init_database_{database_schema_subsection}.sql

- the Dockerfile copy all the .sql files from [init_database](../init_database/) and [update_database](../update_database/) into /docker-entrypoint-initdb.d. As the Dockerfile is built on the basis of the Docker redacted official image, all _.sql_, _.sql.gz_, and _.sh_ files found in the /docker-entrypoint-initdb.d folder are executed at the container launch (see <https://hub.docker.com/_/redacted>, Initialization scripts). Scripts are run in alphabetical order. To ensure the order in which the scripts are run they are prefixed with numbers as {priority_order}.

- "_init_database_" is common to all files

- {database_schema_subsection} specify which part of the database schema is described in the file

## SQL files structure

SQL files are divided in four main sections:

- the "cold tables" corresponding to tables filled by a limited number of constant values, _a priori_ by HRWSI operators. They are not updated by the operational system, but are used as enums by it.

- the "core tables" corresponding to tables filled by the operational system, describing the triggering conditions, processing tasks and products managed by the system.

- the "types". They do not correspond to real objects described by one of the table. They are agregations of attributes from several tables, corresponding to a given need in the system, they are returned by several psql function.

- the "functions", corresponding to specific, complex and custom requests often used by the system. Psql functions can manually be invoked for testing/debug/monitoring purposes, either from VSCode thanks to the postgresql plugin or from the database instance. To call a psql function directly from the shell of the database instance please run

```bash
psql -U redacted -d HRWSI_db -c 'SELECT * FROM hrwsi.function_1(arg1,arg2,...);'
```

## SQL files description

### 0_init_database_set_database.sql

High level sets for the database. Creates the schema, and all extensions needed by the database (the extensions needed by the psql tests are not coded there, as this code main purpose is to be used in production).

### 1_init_database_input.sql

Describes all the tables from the input section. Its functions are mostly oriented toward knowing if an input already exists, if an associated processing task is already created, or to know what the caracteristics of a given input are.

### 2_init_database_processing_tasks.sql

Describes all the tables from the processing tasks section. Its functions are oriented toward knowing if a processing task is finished, geeting information about how a processing task is going, getting logs, etc.

### 3_init_database_products.sql

Describe all the tables from the products section. Its functions are oriented toward knowing the status of indexation processes, getting caracteristics of the delivered products, getting statitstics about the products generations, etc.
