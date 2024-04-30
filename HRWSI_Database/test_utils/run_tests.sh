#!/bin/sh

## Running tests on launched and loaded HRWSI_Database_container DEV VERSION
psql -U redacted  -d hrwsi_db -c 'CREATE extension IF NOT EXISTS "pgtap";'
pg_prove -v --dbname hrwsi_db --username redacted /home/tests/**/*.sql | tee -a /home/hrwsi_db_tests.log