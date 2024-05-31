FROM lis:1.11.0

MAINTAINER Cemal Melih Tanis "cemal.melih.tanis@fmi.fi"

# RUN apt-get update
# RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*
# RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# RUN sh Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda

# ADD env.yml /
# RUN ./miniconda/bin/conda env create -f env.yml

#install programs from source
ADD *.py /opt/sp/
ADD common /opt/sp/common
ADD geometry /opt/sp/geometry
ADD utils /opt/sp/utils
ADD sps1s2.sh /opt/sp/

# ENTRYPOINT ["./miniconda/bin/conda", "run", "--no-capture-output", "-n", "eea_sp"]
