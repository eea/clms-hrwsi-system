#!/bin/sh
tile=$1
year_start=$2
year_end=$((year_start+1))
dm=$3

python /opt/sp/lis_sps1s2_pre_processing.py --gfsc-dir /opt/work/gfsc/${year_start}-${year_end}/T${tile} --input-dir /opt/work/input/${year_start}-${year_end}/T${tile} --output-dir  /opt/work/output/LIS_${year_start}-${year_end}_T${tile} --start-date ${year_start}1001 --end-date ${year_end}0930

FSC_LIST=$(for fsc in `ls /opt/work/input/${year_start}-${year_end}/T${tile}`;do echo -i /opt/work/input/${year_start}-${year_end}/T${tile}/$fsc;done)
python /usr/local/app/let_it_snow_synthesis.py -c /opt/work/config/lis_configuration.json -j /opt/work/config/lis_synthesis_launch_file.json -t ${tile} -o /opt/work/output/LIS_${year_start}-${year_end}_T${tile} -b 01/10/${year_start} -e 30/09/${year_end} --date_margin ${dm} $FSC_LIST

python /opt/sp/lis_sps1s2_post_processing.py --workdir /opt/work --input-folder ${year_start}-${year_end}/T${tile} --output-folder LIS_${year_start}-${year_end}_T${tile}  --tile-id ${tile} --start-date ${year_start}1001 --end-date ${year_end}0930
