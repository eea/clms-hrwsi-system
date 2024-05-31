FROM ubuntu:24.04

LABEL authors="Markus Hetzenecker"
LABEL maintainer="Markus.Hetzenecker@enveo.at"
LABEL Description="HR-WSI SIG0 Processing" Vendor="ENVEO IT" Version="1.0"

# build/run it at ENVEO with
# helpers: --log-level=debug,  --no-cache, --ulimit=nofile=20000:20000
# podman build --tag hrwsi_sig0 -f Dockerfile
# V=""
# for i in opt/wsi/auxiliaries opt/wsi/input; do V="$V -v=$PWD/$i:/$i:ro"; done
# for i in opt/wsi/intermediate opt/wsi/logs opt/wsi/output; do V="$V -v=$PWD/$i:/$i:rw"; done
# podman run -it --rm --user eouser $V hrwsi_sig0 /opt/wsi/processing_routine/hrwsi_process_sig0.py ../input/configuration_file.yml

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

# install SNAP
WORKDIR /src
COPY response.varfile ./
# orig SNAP install url: https://download.esa.int/step/snap/9.0/installers/esa-snap_sentinel_unix_9_0_0.sh
RUN curl -o snap.sh https://projects.enveo.at/EEA_HR-WSI/sources/esa-snap_all_unix_9_0_0.sh && sh ./snap.sh -q -dir /opt/snap  -varfile response.varfile
RUN echo snap.versionCheck.interval=NEVER >> /opt/snap/etc/snap.properties
RUN mv /opt/snap/bin/gpt.vmoptions /opt/snap/bin/gpt.vmoptions.orig
RUN echo /opt/snap/platform/lib > /etc/ld.so.conf.d/snap.conf && /sbin/ldconfig
RUN /opt/snap/bin/snap --nosplash --nogui --modules --update-all 2>&1 | while read -r line; do echo $line; [ "$line" = "updates=0" ] && sleep 2 && pkill -TERM -f "snap/jre/bin/java"; done; /bin/true
RUN su -l eouser -c "/opt/snap/bin/gpt --diag"

##############################

# install Sentinel (Wet) Snow Processing scripts
RUN mkdir -pv /opt/wsi/input /opt/wsi/logs /opt/wsi/intermediate /opt/wsi/output /opt/wsi/auxiliaries /opt/wsi/temp /opt/wsi/software /opt/wsi/processing_routine
RUN chown -v eouser /opt/wsi/logs /opt/wsi/intermediate /opt/wsi/output /opt/wsi/temp
ADD *.py /opt/wsi/processing_routine/

# delete temporary dirs
WORKDIR /opt/wsi/processing_routine/
RUN rm -rf /src /root/.snap /root/.java
