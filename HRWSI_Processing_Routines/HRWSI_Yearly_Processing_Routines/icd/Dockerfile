FROM lis:1.11.0

# change workdir
WORKDIR "/opt/icd"

# install miniconda and python environment
RUN apt-get update
RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN sh Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ADD env.yml .
RUN ./miniconda/bin/conda env create -f env.yml

#install programs from source
ADD icd*.py .
ADD *.xml .
ADD README.md .
ADD validate_cloud_optimized_geotiff.py .
ADD lis_*.json .

ENTRYPOINT ["./miniconda/bin/conda", "run", "--no-capture-output", "-n", "eea_icd"]
