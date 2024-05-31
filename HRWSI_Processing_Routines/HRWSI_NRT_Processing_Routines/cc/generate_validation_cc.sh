#!/bin/bash

export GDAL_NUM_THREADS=ALL_CPUS
L2A_tile=$1
S3CFG_FILE=$2

echo $(date -u) "Working on tile $L2A_tile"
echo $(date -u) "> Preparing work tree..."
rm -rf /opt/work
mkdir /opt/work
mkdir /opt/work/output

echo 'activating micromamba env'
export MAMBA_EXE='/usr/bin/micromamba';
export MAMBA_ROOT_PREFIX='/home/eouser/micromamba';
eval "$(micromamba shell hook --shell bash)"
micromamba activate CC

echo $(date -u) "> Harvesting L2A folders from S3 bucket tf-sip-data..."
L2A_folders=""
months="_202009 _202010 _202011 _202012 _202101 _202102 _202103 _202104 _202105 _202106 _202107 _202108 _202109 _202110 _202111 _202112"
for month in $months
    do echo $(date -u) ">>> Working on month $month..."
    L1C_base_folders=$(s3cmd -c $2 ls s3://tf-sip-data/$L2A_tile/L2A/reference/ | grep $month)
    for L1C_folder in $L1C_base_folders
        do processing_mode_folders=''
        if [[ $L1C_folder != 'DIR' ]]
        then echo $(date -u) ">>>>>> Treating candidate folder $L1C_folder..."
        processing_mode_candidates=$(s3cmd -c $2 ls $L1C_folder)
        for candidate in $processing_mode_candidates
            do if [[ $candidate != 'DIR' ]]
                then processing_mode_folders=$processing_mode_folders" $candidate"
            fi
        done
        fi
        echo $(date -u) ">>>>>> Treating candidate processing base folder(s) $processing_mode_folders..."
        for processing_mode_folder in $processing_mode_folders
            do L2A_base_candidates=$(s3cmd -c $2 ls $processing_mode_folder)
            for candidate in $L2A_base_candidates
                do if [[ $candidate != 'DIR' ]]
                    then L2A_folders=$L2A_folders" $candidate"
                fi
            done
        done
    done
done

echo $(date -u) "> Harvesting and setup done."

for L2A_folder in $L2A_folders
    do echo $(date -u) "> Working on L2A $L2A_folder..."

    echo $(date -u) ">>> Downloading the L2A..."
    L2A_name=(${L2A_folder//\// })
    L2A_name=${L2A_name[-1]}
    echo $(date -u) "L2A name is $L2A_name..."

    mkdir /opt/work/output/$L2A_name
    s3cmd -c $2 get --quiet --recursive $L2A_folder /opt/work/output/$L2A_name
    files=$(ls /opt/work/output/$L2A_name | grep 'SRE')

    if [ -z "$files" ]
        then rm -rf /opt/work/output/$L2A_name
        echo $(date -u) ">>> L2A incomplete, passing..."
        continue
    fi

    echo $(date -u) ">>> Launching the post-processing..."
    python3 maja_cc_post_processing.py --workdir /opt/work --l2a_name $L2A_name
    rm -rf /opt/work/*_tmp

    echo $(date -u) ">>> Uploading result CC to GDrive..."
    CC_folder=$(ls /opt/work | grep CC)
    echo $(date -u) ">>>>>> CC folder is at $CC_folder"
    echo $(date -u) ">>>>>> Uploading to HRWSI_GDrive_data:/10-EEA_HR-WSI_External/4-SoftwareAndData/41-Data/CC/VALIDATION_DATA/$L2A_tile/$CC_folder"
    rclone copy /opt/work/$CC_folder HRWSI_GDrive_data:/10-EEA_HR-WSI_External/4-SoftwareAndData/41-Data/CC/VALIDATION_DATA/$L2A_tile/$CC_folder

    echo $(date -u) ">>> Cleaning work tree..."
    rm -rf /opt/work/output/*
    rm -rf /opt/work/CC*

    echo $(date -u) "> Done."
done


# Pour run ce script il faut au préalable
#     - basic installs (git, docker, tout ce qu'il faut pour S3,etc)
#     - aller sur le worker à /opt/src. Git clone le repo CC
#     - lancer ce script
