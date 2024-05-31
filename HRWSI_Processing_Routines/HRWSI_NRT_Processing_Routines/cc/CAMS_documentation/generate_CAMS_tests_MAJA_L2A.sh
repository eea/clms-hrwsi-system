#! /bin/bash

declare -a date_list=("0905" "0908" "0910" "0911" "0913" "0915" "0916" "0918" "0920" "0928" "0930" "1001" "1008" "1013" "1018" "1025" "1028" "1030" "1031")

for date in "${date_list[@]}"
do
	l1c_name=$(rclone lsf HR-WSI:10-EEA_HR-WSI_External/4-SoftwareAndData/41-Data/MAJA/L1C/32TNS | grep 2020"$date")
	rclone copy HR-WSI:10-EEA_HR-WSI_External/4-SoftwareAndData/41-Data/MAJA/L1C/32TNS/"$l1c_name" /opt/work/maja_inputs
	
	mv /opt/L2A/32TNS/* /opt/work/maja_inputs
	
	./opt/MAJA-4.8.0/bin/maja -i /opt/work/maja_inputs -w /opt/work/workdir -o /opt/L2A/32TNS -ucs /opt/userconf -m L2NOMINAL > log_nominal_120_no_cams_2020"$date".txt

	rclone copy /opt/L2A/32TNS/ HR-WSI:07-Technique/72-Données/722-L2A-MAJA/MAJA-4.8/32TNS/NO_CAMS_120_from_september/

	rm -rf /opt/work/"$l1c_name"
	rm -rf /opt/work/SENTINEL*
done


