# How to use this Dockerfile

## Retrieve OTB 7
OTB and its dependances can be retrieved at https://www.orfeo-toolbox.org/
We need :
* otb.tar.gz 
* SuperBuild-archives.tar.bz2 

## Retrieve LIS
LIS can be retrieve from this repository by git clone and compress into the Docker context as lis.tar.gz

## Build
`docker build -t lis .`

## Run 
`docker run --rm -it lis`

or define an entrypoint