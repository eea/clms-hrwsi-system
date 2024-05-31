# get and update Ubuntu
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# change workdir
WORKDIR "/opt/wics1"

# install miniconda and python environment
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN sh Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ADD env.yml .
RUN ./miniconda/bin/conda env create -f env.yml

#install programs from source
ADD wics1*.py .
ADD *.xml .
ADD README.md .
ADD validate_cloud_optimized_geotiff.py .

ENTRYPOINT ["./miniconda/bin/conda", "run", "--no-capture-output", "-n", "eea_wics1"]
