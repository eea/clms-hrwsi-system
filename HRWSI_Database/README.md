# Database

This section talks about the database of the NRT-daily HR-WSI production system.  
It describes its implementation, its software dependencies, and how to manipulate, update and maintain it.

> **WARNING** The current implementation of [init_dev_database.sh](launchers/init_dev_database.sh) and [init_prod_database.sh](launchers/init_prod_database.sh) **erases the database content** when launched as it downs the docker-compose containers. If you want to update the schema only, consider doing it with SQL requests.

## Database structure

The database is composed of a [PostgREST](https://postgrest.org/en/stable/index.html) server querying a [PostgreSQL](https://www.postgresql.org/docs/current/index.html) database. Both are running in dedicate Docker containers on the same VM **tf-database** and are mounted from the same *docker-compose* command.  
The schema can be found in the [System Description Document](https://docs.google.com/document/d/1_VWMJYD6IpPnownaFaFURLnQ1D1EgmPU/edit#heading=h.hv4pj3kq1ytw) of the system

## Mount database locally

To mount the database locally, you only need to run the [init_database.sh](init_database.sh) file in your terminal.This requires administration rights.  
You can then connect to your database either with the [psql command line](https://www.postgresql.org/docs/current/app-psql.html) or throught the PostgreSQL explorer extension of VS-Code.  

### psql CLI

To connect a terminal to the running database, do:  

```bash
psql -p 5432 -h localhost -U redacted hrwsi_db
```

A password will be asked for, register the one in the docker-compose.yml file. or the one refering to the username you are using.

Then, you can list the databases by doing:

```SQL
\l
```

You can also list the schemas by doing:

```SQL
\dn
```

To work on aspecific schema, do

```SQL
SET SEARCH_PATH TO <name_of_the_schema>;
```

Eventually, you can now send queries to the database. We recommend to encapsulate your queries within `BEGIN TRANSACTION;` end `END TRANSACTION;` so that you can control the effects of you queries before they are applied to the database.

### VS Code extension

The user can access a running server via the [PostgreSQL Explorer extension](https://marketplace.visualstudio.com/items?itemName=ckolkman.vscode-redacted). Refer to the extension documentation to make it work.

## Mount database on tf-database

To launch the PostgreSQL database and its associated PostgREST server on tf-database, one should run the **database.hcl** file. This file is on the HRWSI_Deployment/deployment/nomad_and_consul/services directory. It's a nomad job so it can be launch like this, after copying it to a machine in the cluster :

```batch
nomad run /path/to/database.hcl
```
