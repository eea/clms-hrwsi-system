FROM ubuntu:24.04

LABEL authors="Markus Hetzenecker"
LABEL maintainer="Markus.Hetzenecker@enveo.at"
LABEL Description="HR-WSI SWS Processing" Vendor="ENVEO IT" Version="1.0"

# build/run it at ENVEO with
# helpers: --log-level=debug,  --no-cache, --ulimit=nofile=20000:20000, --root=/srv/containers/$USER/storage
# podman build --tag hrwsi_sws -f Dockerfile
# V=""
# for i in opt/wsi/auxiliaries opt/wsi/input; do V="$V -v=$PWD/$i:/$i:ro"; done
# for i in opt/wsi/intermediate opt/wsi/logs opt/wsi/output; do V="$V -v=$PWD/$i:/$i:rw"; done
# podman run -it --rm --user eouser $V hrwsi_sws /opt/wsi/processing_routine/hrwsi_process_sws.py ../input/configuration_file.yml

ENV TZ="UTC"
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
    
#basic system installs
RUN apt-get update -y --fix-missing && apt-get -y upgrade
RUN apt-get install -y --fix-missing curl python3 python3-numpy python3-scipy python3-yaml python3-requests gdal-bin python3-gdal python3-dateutil python3-boto3

# create user
RUN groupadd eouser && useradd -m -g eouser -s /bin/bash eouser

##############################

WORKDIR /src

# # install Sentinel (Wet) Snow Processing scripts
RUN mkdir -pv /opt/wsi/input /opt/wsi/logs /opt/wsi/intermediate /opt/wsi/output /opt/wsi/auxiliaries /opt/wsi/temp /opt/wsi/software /opt/wsi/processing_routine
RUN chown -v eouser /opt/wsi/logs /opt/wsi/intermediate /opt/wsi/output /opt/wsi/temp
ADD *.py /opt/wsi/processing_routine/

#delete src dir
WORKDIR /opt/wsi/processing_routine/
RUN rm -rf /src
