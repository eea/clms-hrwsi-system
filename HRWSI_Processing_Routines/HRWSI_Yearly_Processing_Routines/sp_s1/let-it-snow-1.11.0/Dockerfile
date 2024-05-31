ARG REGISTRY_URL
FROM ${REGISTRY_URL}ubuntu:20.04 as builder

# Reference : https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.authors="aurore.dupuis@cnes.fr vincent.gaudissart@csgroup.eu celine.raille@thalesgroup.com"
LABEL org.opencontainers.image.description="LIS Build container"

# Montage du volume temporaire et utilisation pour apt le site du cnes
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
	apt-get update -y && \
    apt-get install -y ca-certificates 

#Ajout des certificats
#COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Install required packages
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
	apt-get update -y --quiet && \
    DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes --no-install-recommends \
        # basic system installs
        build-essential \
        python3 \
        python3-pip \
        software-properties-common \
        git \
        wget \
        tar \
        unzip \
        # packages needed for compilation
        cmake \
        swig \
        ninja-build \
        python3-dev \
        pkg-config \
        libinsighttoolkit4-dev \
        libopenthreads-dev \
        libossim-dev \
        libtinyxml-dev \
        libmuparser-dev \
        libmuparserx-dev \
        libfftw3-dev \
        libgsl-dev \
        mono-runtime-common \
        && \
    DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes --no-install-recommends \
        # optional packages for OTB compilation
        python3-vtkgdcm \
        libvtkgdcm-cil \
        libvtkgdcm-java \
        libgdcm-tools \
        && \
    add-apt-repository ppa:ubuntugis/ubuntugis-unstable --yes && \
    DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes --no-install-recommends \
        # GDAL \
        libgdal-dev \
        python3-gdal \
        gdal-bin \
        && \
    rm -rf /var/lib/apt/lists/*

# Build OTB    
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
    ln -s /usr/lib/cli/vtkgdcm-sharp-3.0/libvtkgdcmsharpglue.so /usr/lib/x86_64-linux-gnu/libvtkgdcmsharpglue.so && \
    mkdir -p /usr/lib/python/dist-packages && \
    ln -s /usr/lib/python3/dist-packages/vtkgdcmPython.cpython-38-x86_64-linux-gnu.so /usr/lib/python/dist-packages/vtkgdcmPython.so && \
    mkdir -p /root/otb-build/build && \
    cd /root/otb-build && \
    # wget -q --ca-certificate=/usr/local/share/ca-certificates/ca-bundle.crt https://www.orfeo-toolbox.org/packages/archives/OTB/OTB-7.4.2.tar.gz -O /tmp/OTB.tar.gz && \
    wget -q https://www.orfeo-toolbox.org/packages/archives/OTB/OTB-7.4.2.tar.gz -O /tmp/OTB.tar.gz && \
    tar -xvzf /tmp/OTB.tar.gz && \
    cd /root/otb-build/build && \
    cmake \
        "-DBUILD_COOKBOOK:BOOL=OFF" \
        "-DBUILD_EXAMPLES:BOOL=OFF" \
        "-DBUILD_TESTING:BOOL=OFF" \
        "-DBUILD_SHARED_LIBS:BOOL=ON" \
        "-DOTB_WRAP_PYTHON:BOOL=ON" \
        "-DOTB_USE_MUPARSER:BOOL=ON" \
        "-DOTB_USE_MUPARSERX:BOOL=ON" \
        "-DOTB_USE_SIFTFAST:BOOL=ON" \
        "-DOTB_USE_SPTW:BOOL=ON" \
        "-DOTB_USE_SSE_FLAGS:BOOL=ON" \
        "-DOTB_USE_LIBKML:BOOL=ON" \
        "-DModule_OTBTemporalGapFilling:BOOL=ON" \
        "-DModule_SertitObject:BOOL=ON" \
        "-DModule_otbGRM:BOOL=ON" \
        "-DCMAKE_BUILD_TYPE=Release" \
        -DCMAKE_INSTALL_PREFIX="/install/otb" -GNinja .. && \
    ninja install && \
    rm -rf /root/otb-build /tmp/OTB.tar.gz

# Build LIS
ADD . /LIS_src/
RUN  ln -s /usr/bin/python3 /usr/bin/python && \
     mkdir -p /root/lis-build && \
     cd /root/lis-build && \
     cmake -DCMAKE_PREFIX_PATH=/install/otb \
          -DCMAKE_INSTALL_PREFIX=/install/lis /LIS_src/ && \
     make -j 6 && \
     make install && \
     chmod a+x /install/lis/app/*

# Build DANS-GDAL scripts
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
	mkdir -p /root/dans-build && \
    cd /root/dans-build && \
    # wget -q --ca-certificate=/usr/local/share/ca-certificates/ca-bundle.crt https://github.com/gina-alaska/dans-gdal-scripts/archive/refs/heads/master.zip -O /tmp/dans.zip && \
    wget -q https://github.com/gina-alaska/dans-gdal-scripts/archive/refs/heads/master.zip -O /tmp/dans.zip && \
    unzip /tmp/dans.zip && \
    cd dans-gdal-scripts-master && \
    ./autogen.sh && \
    ./configure --prefix=/install/dans && \
    make && \
    make install && \
    rm -rf /root/dans-build /tmp/dans.zip

##############################
#ARG REGISTRY_URL
FROM ${REGISTRY_URL}ubuntu:20.04

LABEL org.opencontainers.image.authors="aurore.dupuis@cnes.fr vincent.gaudissart@csgroup.eu celine.raille@thalesgroup.com"
LABEL org.opencontainers.image.description="LIS + OTB 7.4 Container"

# system packages
#COPY cert[s]/* /usr/local/share/ca-certificates/
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
    apt-get update -y --quiet && \
    DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes --no-install-recommends \
        ca-certificates \
        file \
        git \
        libpython3.8 \
        python3 \
        python-is-python3 \
        python3-pip \
        python3-lxml \
        software-properties-common \
        # for OTB
        libinsighttoolkit4.13 \
        libopenthreads21 \
        libossim1 \
        libtinyxml2.6.2v5 \
        libmuparser2v5 \
        libmuparserx4.0.7 \
        libfftw3-3 \
        libgsl23 \
        libgslcblas0 \
        && \
    # GDAL
    add-apt-repository ppa:ubuntugis/ubuntugis-unstable --yes && \
	DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes --no-install-recommends \
        # GDAL \
        libgdal30 \
        python3-gdal \
        gdal-bin \
        && \
    rm -rf /var/lib/apt/lists/*

# install OTB from builder
COPY --from=builder /install/otb /usr/local
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
ENV OTB_APPLICATION_PATH=/usr/local/lib/otb/applications/
ENV PYTHONPATH=$PYTHONPATH:/usr/local/lib/otb/python:/usr/local/lib/python3.8/site-packages/
ENV PATH=/usr/local/app:/usr/local/bin:$PATH

# install LIS from builder
COPY --from=builder /install/lis /usr/local
RUN mv /usr/local/lib/otbapp_* /usr/local/lib/otb/applications/

# install DANS GINA from builder
COPY --from=builder /install/dans /usr/local

# install rastertools and additionnal dependancies
ARG GIT_USER
ARG GIT_TOKEN
COPY rastertools-33-open-source /tmp/rastertools
RUN if [ -f "/kaniko/run/secrets/http_proxy" ]; then export http_proxy=$(cat /kaniko/run/secrets/http_proxy); export https_proxy=$(cat /kaniko/run/secrets/https_proxy); fi && \
    mkdir -p /install && \
    cd /install && \
    mv /tmp/rastertools /install &&\
    #git -c http.sslVerify=false clone --branch master https://${GIT_USER}:${GIT_TOKEN}@gitlab.cnes.fr/eolab/processing/rastertools.git && \
    export PYTHONWARNINGS="ignore:Unverified HTTPS request" && \
    python3 -m pip install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --no-cache-dir --ignore-installed -U\
    numpy \
    setuptools \
    setuptools_scm wheel \
    && \
    python3 -m pip install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --no-cache-dir \
    /install/rastertools \
    geopandas \
    pyscaffold \
    matplotlib \
    rasterio \
    scipy \
    tqdm \
    && \
    rm -r /install

ENV GDAL_NUM_THREADS=ALL_CPUS