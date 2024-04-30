# PSQL Tests

## Purpose and general presentation

Just as any other part of the HR-WSI system, we aim to test the SQL code we use for the database.

A first level of test consists in using the .sql scripts to instantiate the database container. This tests the correctness of the init_database and update_sql scripts syntax as syntaxic error would raise errors during instanciation.
Additionaly, we want to assert that the tables, the functions and the indexes of the database are compliant with what is described in the SDD and milestones of the operational system on GitLab.

A few technologies can be used to test PostgreSQL code. We chose to use pgTap, as it is relatively recent, and documentation/tutorials can be found on the Internet.

About pgTap, here are a few links holding documentation:
- [main page for pgTap presentation](https://pgtap.org/)
- [pgTap installation](https://pgxn.org/dist/pgtap/)
- [beginner's guide](https://pgxn.org/dist/pgtap/doc/pgtap.html)
- [pgTap functions complete documentation](https://pgtap.org/documentation.html)

Some fotume posts and others were of great help to set up a first draft of tests with pgTap :
- https://medium.com/engineering-on-the-incline/unit-testing-redacted-with-pgtap-af09ec42795
- https://medium.com/engineering-on-the-incline/unit-testing-functions-in-postgresql-with-pgtap-in-5-simple-steps-beef933d02d3

## Installation of pgTap

The pgTap installation steps are described in the HR-WSI database [Dockerfile](/HRWSI_Database/Dockerfile), section "dev". A few Linux libraries need to be installed first. They are linked to Perl and PostgreSQL environments, as pgTap is a Perl-based test utility for testing PostgreSQL code.
pgTab third-part dependencies are:

- build-essential
- libicu-dev
- postgresql-client
- postgresql-server-dev-all

The pgTap zip archive can then be downloaded for version 1.1.0 can be found [here](https://api.pgxn.org/dist/pgtap/1.1.0/pgtap-1.1.0.zip). Once unziped, and installed with the help of CPAN (Comprehensive Perl Archive Network, see the [main page](https://www.cpan.org/)); `make` and `make install` steps finalize the installation.

As pgTap is a PostgreSQL testing utility, it has to be installed in a PostgreSQL environment (for example on a Docker image from [redacted official image hub](https://hub.docker.com/_/redacted)), and then to be linked with a PostgreSQL database.

## Running pgTap tests on a DB

The first step is to launch a database/server duet using [init_dev_database.sh](/HRWSI_Database/init_dev_database.sh).  
The database that is to be tested needs to be upgraded with the pgTap extension. In HR-WSI, we chose not to create the extension directly in the schema to avoid having this extension installed in production. We "manually" add the extension as a part of the testing process with the command:

```bash
psql -U redacted -d hrwsi_db -c 'CREATE extension IF NOT EXISTS "pgtap";'
```

resp. if pgTap tests are not on the same machine as the database, use:

```bash
sudo docker exec -it HRWSI_Database_hrwsi_db_container_1 bash -c  "psql -U redacted -d hrwsi_db -c 'CREATE extension IF NOT EXISTS "pgtap";'"
```

corresponding to the particular case of pgTap being run on a local machine, on which a Docker container with the database would be run.

To run the tests we use pg_prove (documentation can be found [here](https://pgtap.org/pg_prove.html)). It is installed with pgTap. The command is:

```bash
pg_prove -v --dbname hrwsi_db --username redacted /home/tests/**/*.sql
```

Resp. when the tests are run from outside the machine on which the database is deployed

```bash
sudo docker exec -it HRWSI_Database_hrwsi_db_container_1 bash -c "pg_prove -U redacted -d hrwsi_db /home/tests/**/*.sql"
```

The latter are used in the CI-CD chain to test the database remotely.

## Tests directory structure

In the test folder we create subfolders to test the tables (tables) and the functions (functions).

In the tables folder, we created a sql file for each table described in the various .sql files from init_database folder.

In the functions folder we created one sql file to test for all the functions in each .sql files from init_database folder. An evolution that may be required would be to separate the tests for each function in a dedicated file. Indeed the thorough tests can be very dense and lead to long test files, with reduced lisibility. Though it might be an issue as most of the mocked content of the database, that is needed as a set up for the tests of the functions, can be used to test several functions. So far it seems not to be possible to use a common set up plan if the tests are separated in many sql files. (TO BE INVESTIGATED)

pgTap is providing a test report with information, sql file by sql file, on the passed and failed tests. It provides basic debug information in case of failure. More accurate error message can be customized in case of an expected (possible or reccurent) test failure.

It is possible (for debug purposes or specific testing) to target a given .sql test file with the following command:

```bash
pg_prove -v --dbname hrwsi_db --username redacted /home/tests/given_folder/given_file.sql
```

## Miscellanious about a pgTap test structure

### Header and footer of a pgTap test script

Two common parts can be found at the beginning and the end of the tests.

A test file begins with these two lines:

```bash
BEGIN;

SELECT plan(3);
```

The number of tests in the sql file is to be specified in "plan(<exact_number_of_tests>)". If the number in less than the total number of tests in the file, some will be ignored and an error might be raised.

A test file ends with these two lines:

```bash
SELECT * FROM finish();

ROLLBACK
```

It cleans the mocked database and ensure independance between tests.

### Table-test structure

As described in pgTap documentation many tests can be performed on tables, including testing the conditions set on some columns, the attributes of a table, etc...

Since the HR-WSI database is relatively simple regarding that apsect, we chose to test lightly the tables. We check the attributes of each table, and the foreign keys constraints.

### Function-test structure

As described in pgTap documentation many tests can be performed on functions. As the functions currently implemented in HR-WSI remain relatively simple, we chose to test simple things.

First we check the existence of the various expected psql functions (meaning, the name exist, it is reachable, the input parameters are the ones expected) then we check that the return type of these functions is the one expected.

The second main check tackles the behavior of the functions. We perform basic unit testing. Most of the functions currently coded have a straightforward behavior and are tested only for the success of the nominal behavior.
To perform unit testing the content of the database need to be mocked accordingly to a test case situation. Several steps are followed:

- Feed data in the  mocked database. It is done by inserting made up rows in the minimal compulsory tables
- Prepare statements. We prepare the call to the tested functions, and made up responses corresponding to the expected response
- Test functions. We compare the output of the prepared statement from the function call to the prepare statement from the mocked expected reponse.
