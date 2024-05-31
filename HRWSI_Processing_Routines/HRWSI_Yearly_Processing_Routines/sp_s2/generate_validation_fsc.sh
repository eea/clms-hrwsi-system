#!/bin/sh

LIST_L2A=''#insert code to look through the S3 bucket for a given tile
cp -r /opt/src/FSC/config /opt/work/config

for L2A in "${LISTE_L2A[@]}"
do
    #download L2A from S3 bucket
    mv /path/to/download/$L2A /opt/work/L2A/$L2A
    docker run --name lis_1-11-0_worker --entrypoint /usr/local/fsc/run_LIS_processing_and_postprocessing.sh -v /opt/work:/opt/work -v /opt/src/fsc:/usr/local/fsc lis_1-11-0

    rm -rf /opt/work/*_tmp
    #upload FSC for /opt/work to S3 bucket

    rm -rf /opt/work/L2A/*
    rm -rf /opt/work/output
    rm -rf /opt/work/FSC*
    docker container rm lis_1-11-0_worker
done


# Pour run ce script il faut au préalable
#     - basic installs (git, docker, tout ce qu'il faut pour S3,etc)
#     - aller sur le worker à /opt/src. Git clone le repo FSC
#     - build l'image de LIS, ou la récupérer d'une registry
#     - récupérer tous les auxilliaires de la tuile à traiter et les ranger dans /opt/work (en respectant les noms de dossiers, voir REAMDE.md)
#     - update le launch_configuration_file.json avec les bons noms de fichiers auxilliaires et de tuiles
#     - update ce script avec la récupération des L2A, le path où ils seront download, et l'upload des FSC
#     - lancer ce script