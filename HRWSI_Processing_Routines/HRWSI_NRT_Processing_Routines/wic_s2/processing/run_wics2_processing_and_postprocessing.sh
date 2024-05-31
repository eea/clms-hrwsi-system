#!/bin/sh

CONFIG_PATH="/path/to/config_classifier.json"

python processing/l2a_to_WIC_RF.py $CONFIG_PATH
python processing/wics2_post_processing.py $CONFIG_PATH

