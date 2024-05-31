#!/bin/sh

L2A_NAME=$( ls /opt/work/L2A ) 

python /usr/local/app/let_it_snow_fsc.py -j /opt/work/config/launch_configuration_file.json -i /opt/work/L2A/$L2A_NAME

python /usr/local/fsc/lis_fsc_post_processing.py --workdir /opt/work --l2a_name $L2A_NAME