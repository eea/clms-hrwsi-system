# Database

This section talks about the database of the NRT-daily HR-WSI production system.  
It describes its implementation, its software dependencies, and how to manipulate, update and maintain it.

> **WARNING** The current implementation of `init_database.sh` **erases the database content** when launched as it downs the docker-compose containers. If you want to update the schema only, consider doing it with SQL requests.

## Database structure

The database is composed of a [PostgREST](https://postgrest.org/en/stable/index.html) server querying a [PostgreSQL](https://www.postgresql.org/docs/current/index.html) database. Both are running in dedicate Docker containers on the same VM **tf-database** and are mounted from the same *docker-compose* command.  
The schema can be found in the [System Description Document](https://docs.google.com/document/d/1_VWMJYD6IpPnownaFaFURLnQ1D1EgmPU/edit#heading=h.hv4pj3kq1ytw) of the system

## Mount database locally

To mount the database locally, you only need to run the [init_database.sh](init_database.sh) file in your terminal.This requires administration rights.  
You can then connect to your database either with the [psql command line](https://www.postgresql.org/docs/current/app-psql.html) or throught the PostgreSQL explorer extension of VS-Code.  

### psql CLI

To connect a terminal to the running database, do:  

```bash
psql -p 5432 -h localhost -U postgres hrwsi_db
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

Eventually, you can now send queries to the database. We recommend to encapsulate your queries within BEGIN TRANSACTION; end END TRANSACTION; so that you can control the effects of you queries before they are applied to the database.

### VS Code extension

The user can access a running server via the [PostgreSQL Explorer extension](https://marketplace.visualstudio.com/items?itemName=ckolkman.vscode-postgres). Refer to the extension documentation to make it work.

## Mount database on tf-database

> This methodology is to be updated once this can be done via the CI/CD chain. The methodology currently used is a work-around the fact that the CI/CD nodes cannot connect themselves to VMs through SSH tunnels.

To launch the PostgreSQL database and its associated PostgREST server on tf-database, one should run *temporary_database_deployer.sh*. This file will, in order:

1. Install Terraform
2. Parametrize Terraform for the OpenStack project
3. Initialize Terraform database provider
4. install jq - to be used to read and format JSONs in bash context using 

``` bash
terraform output -json database_external_private_key | jq -r '' > database_admin_id_rsa
```

5. Extract connection data from database_tfstate.tfstate - which is why we need to have the Terraform background initialized
6. Send docker-compose.yml, Dockerfile, and init_database.sql to tf-database - files used by init_database.sh
7. Run init_database.sh on tf-database through ssh
8. Open a SSH tunnel between tf-database 5432 port and localhost 63333 port

The last operation authorizes the user to connect itself to the tf-database PostgREST server via the psql CLI as follow:

```bash
psql -h localhost -p 63333 -U postgres hrwsi_db
```

It also authorizes the user to access this server via the [PostgreSQL Explorer extension](https://marketplace.visualstudio.com/items?itemName=ckolkman.vscode-postgres) on localhost and port 63333.

If you already have a process listening to port 63333, you can either change the port you want to link to tf-database 5432 or run `sudo lsof -i -P -n | grep 63333` to know what process to kill.