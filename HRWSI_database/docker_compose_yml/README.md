# Docker compose

Docker-compose - not to be confused with now existing docker compose - is a tool to mount a complete docker containers architecture from a yml file. It has the same spirit as Hashicorp in providing infrastructure as a file.  
In the frame of this project, we are using docker-compose to launch various configurations of the database server/instance pair according to the context.  

## How to launch a docker-compose

To launch the containers architecture described in a docker-compose yaml file, you need to use:

``` bash
docker-compose -f <path_to_your_file> up -d
```

The *-d* argument hides the logs and make frees the access to the terminal. It can be removed tob have access to the logs.  
To stop and remove all containers and networks built by the docker-compose, use:

``` bash
docker-compose -f <path_to_your_file> down
```

More information and commands can be found on the [official page](https://github.com/docker/compose)

## Crucial elements about docker-compose use

First, the version used is **3.7** as it is the most recent compliant with our use of Docker images.  
We also custome named the Docekr containers we launch. If you stop and remove the Docker containers without using `docker-compose down`, check that the networks have been removed to with `docker network list`. If not; remove them or the next `docker-compoe up` command will fail.

## Docker-compose files

We have 3 different docker-compose yml files in the frame of the project. All of them have the same generic frame apart from the differences listed below:

- [docker-compose.prod.yml](docker-compose.prod.yml) is to be used when deploying the operationnal database. It does not holds the required extensions and utils to run the tests. It does compile the Docker image of the DB at launch.
- [docker-compose.dev.yml](docker-compose.dev.yml) is to be used to launch a DB locally and run tests on it. It does compile the Docker image of the DB at launch.
- [docker-compose.CI.yml](docker-compose.CI.yml) is to be used to launch a DB by GitLab CICD cahin and run tests on it. It does NOT compile the Docker image of the DB at launch.