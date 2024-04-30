FROM postgres:latest AS base

LABEL maintainers: "robin.buratti@magellium.fr, adrien.ceschin@magellium.fr"

COPY init_database /docker-entrypoint-initdb.d/
COPY update_database /docker-entrypoint-initdb.d/

# The following part is to be mounted and used only in CI-CD or locally when testing the DB.
# It is not meant to be deployed on the NRT production system.

FROM base AS dev

RUN apt update && apt-get install --yes\
  build-essential \
  libicu-dev \
  unzip \
  wget

WORKDIR /home
RUN wget https://api.pgxn.org/dist/pgtap/1.1.0/pgtap-1.1.0.zip && \
  unzip pgtap-1.1.0.zip && \
  cd pgtap-1.1.0 && \
  cpan TAP::Parser::SourceHandler::pgTAP && \
  cpan TAP::Harness::Archive &&\
  make && \
  make install

COPY tests /home/tests

# Required to store tests results at run
RUN touch /home/hrwsi_db_tests.log && chmod 777 /home/hrwsi_db_tests.log
COPY test_utils/run_tests.sh /docker-entrypoint-initdb.d/
