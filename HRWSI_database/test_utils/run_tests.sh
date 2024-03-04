#!/bin/sh

## Running tests on launched and loaded hrwsi_database_container DEV VERSION
psql -U postgres  -d hrwsi_db -c 'CREATE extension IF NOT EXISTS "pgtap";'
pg_prove -U postgres -d hrwsi_db /home/tests/**/*.sql >> /home/hrwsi_db_tests.log
