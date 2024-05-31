#!/bin/bash

L2A_tile=$1

echo $(date -u) "Working on tile $L2A_tile"
echo $(date -u) "> Preparing work tree..."

rm -rf /opt/work
mkdir /opt/work
mkdir /opt/work/DEM/
mkdir /opt/work/tcd/
mkdir /opt/work/water_mask/
mkdir /opt/work/L2A

echo $(date -u) "> Identifying auxiliaries on GDrive..."
GDRIVE_AUX_ROOT='HRWSI_GDrive_data:/10-EEA_HR-WSI_External/4-SoftwareAndData/41-Data'
WL_file=$(rclone lsf $GDRIVE_AUX_ROOT/HRL/Water_Layer_2018/20m | grep $L2A_tile)
TCD_file=$(rclone lsf $GDRIVE_AUX_ROOT/HRL/TCD_2018/20m | grep $L2A_tile)
DEM_file=$(rclone lsf $GDRIVE_AUX_ROOT/DEMs/413_DEM_20m_S2tiled/20m | grep $L2A_tile)

echo $(date -u) "> Dowloading Auxiliaries from GDrive..."
rclone copy $GDRIVE_AUX_ROOT/HRL/Water_Layer_2018/20m/$WL_file /opt/work/water_mask
rclone copy $GDRIVE_AUX_ROOT/HRL/TCD_2018/20m/$TCD_file /opt/work/tcd
rclone copy $GDRIVE_AUX_ROOT/DEMs/413_DEM_20m_S2tiled/20m/$DEM_file /opt/work/DEM

echo $(date -u) "> Creating empty WL..."
export MAMBA_EXE='/usr/bin/micromamba';
export MAMBA_ROOT_PREFIX='/home/eouser/micromamba';
eval "$(micromamba shell hook --shell bash)"
micromamba activate FSC
zero_WL_file='zero_'$WL_file
python3 ~/fsc/utils/create_blank_raster_from_source.py --input /opt/work/water_mask/$WL_file --output /opt/work/water_mask/$zero_WL_file

echo $(date -u) "> Rewritting configuration file at ~/fsc/config/launch_configuration_file.json..."
echo "{
  'input_dir'           : '/opt/work/L2A',
  'output_dir'          : '/opt/work/output',
  'dem'                 : '/opt/work/DEM/$DEM_file',
  'tcd'                 : '/opt/work/tcd/$TCD_file',
  'log'                 : 'INFO',
  'water_mask'          : '/opt/work/water_mask/$zero_WL_file',
  'config_file'         : '/opt/work/config/lis_configuration.json',
  'chain_version'       : '1.11.0',
  'product_counter'     : '1'
}" | sed "s/'/\"/g" > ~/fsc/config/launch_configuration_file.json

echo $(date -u) "> Copying config from ~/fsc/config to /opt/work..."
cp -r ~/fsc/config /opt/work

echo $(date -u) "> Harvesting L2A folders from GDrive..."
GDRIVE_L2A_ROOT="HRWSI_GDrive_data:07-Technique/72-Données/722-L2A-MAJA/MAJA-4.8/32TNS/CAMS_120_from_september"
GDRIVE_FSC_ROOT="HRWSI_GDrive_data:07-Technique/72-Données/724-LIS-FSC/MAJA-4.8/32TNS/CAMS_120_from_september"
L2A_folders=$(rclone lsf $GDRIVE_L2A_ROOT | grep SENTINEL2)

echo $(date -u) "> Harvesting and setup done."
for L2A_folder in $L2A_folders
    do echo $(date -u) "> Working on L2A $L2A_folder..."

    echo $(date -u) ">>> Downloading the L2A..."
    L2A_name=(${L2A_folder//\// })
    L2A_name=${L2A_name[-1]}
    echo $(date -u) "L2A name is $L2A_name..."

    mkdir /opt/work/L2A/$L2A_name
    rclone copy $GDRIVE_L2A_ROOT/$L2A_folder /opt/work/L2A/$L2A_name --progress --transfers=20 --checkers=20
    files=$(ls /opt/work/L2A/$L2A_name | grep 'SRE')

    if [ -z "$files" ]
        then rm -rf /opt/work/L2A/$L2A_name
        echo $(date -u) ">>> L2A incomplete, passing..."
        continue
    fi

    echo $(date -u) ">>> Launching the Docker container..."
    docker rm FSC_worker
    docker run --name FSC_worker --entrypoint /usr/local/fsc/run_LIS_processing_and_postprocessing.sh -v /opt/work:/opt/work -v /home/eouser/fsc:/usr/local/fsc lis_1-11-0 -q
    rm -rf /opt/work/*_tmp

    echo $(date -u) ">>> Uploading result FSC to GDrive..."
    FSC_folder=$(ls /opt/work | grep FSC)
    echo $(date -u) ">>>>>> FSC folder is at $FSC_folder"
    echo $(date -u) ">>>>>> Uploading to $GDRIVE_FSC_ROOT/$L2A_tile/$FSC_folder"
    rclone copy /opt/work/$FSC_folder $GDRIVE_FSC_ROOT/$FSC_folder --transfers=20 --checkers=20
    rclone copy /opt/work/output $GDRIVE_FSC_ROOT/$FSC_folder/output --transfers=20 --checkers=20
    
    echo $(date -u) ">>> Cleaning work tree..."
    rm -rf /opt/work/L2A/*
    rm -rf /opt/work/output
    rm -rf /opt/work/FSC*

    echo $(date -u) "> Done."
done
docker rm FSC_worker

# Pour run ce script il faut au préalable
#     - basic installs (git, docker, tout ce qu'il faut pour S3,etc)
#     - aller sur le worker à /opt/src. Git clone le repo FSC
#     - build l'image de LIS, ou la récupérer d'une registry
#     - récupérer tous les auxilliaires de la tuile à traiter et les ranger dans /opt/work (en respectant les noms de dossiers, voir REAMDE.md)
#     - update le launch_configuration_file.json avec les bons noms de fichiers auxilliaires et de tuiles
#     - update ce script avec la récupération des L2A, le path où ils seront download, et l'upload des FSC
#     - lancer ce script
