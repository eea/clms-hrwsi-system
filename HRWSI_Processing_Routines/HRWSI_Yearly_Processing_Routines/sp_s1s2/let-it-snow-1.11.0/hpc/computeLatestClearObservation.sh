#!/bin/bash
#
# Copyright (C) 2005-2019 Centre National d'Etudes Spatiales (CNES)
#
# This file is part of Let-it-snow (LIS)
#
#     https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Script to make a composite of the latest clear-sky observations over the past nDays since now
# usage: ./computeLatestClearObservation.sh tileId inputDir outputDir nDays
# example: ./computeLatestClearObservation.sh 31TCH /work/OT/siaa/Theia/Neige/Theia/ /tmp/ 20
# output: geotiff file with colormap cyan=snow, grey=no-snow, white=cloud, black=no-data

# Tile ID (ex. 31TCH)
tileId=$1
# Input directory where to look for the products
inputDir=$2
# Output directory
outputDir=$3
# Number of days to go back
nDays=$4
# Today in yyyymmdd format
today=$(date +"%Y%m%d")
# Name of the output composite
outputFn="${outputDir}/LCO_${tileId}_${today}.tif"
# Temporary file
tmpFn="${outputDir}/tmp_${tileId}_${today}.tif"
# Get date list of the n latest days
dateList=$(for i in $(seq $nDays); do date -d "$today -$i day" +"%Y%m%d"; done)
# Search matching products in the tile folder and store in an array
productList=($(for d in ${dateList}; do find ${inputDir} -name "SENTINEL2[A,B]_${d}*${tileId}*SNW_R2.tif"; done))
# Test if the product list is empty
if [ -z "$productList" ]
then
    # No products available: exit
    echo "could not find products matching these dates: "$dateList
    exit 1
else
    # Load OTB
    module load otb/7.0
    # Number of products to be composited
    nProduct=${#productList[@]}
    # Init band math expression
    cmd=im1b1
    # Build band math expression
    for i in $(seq $((nProduct-1))); do cmd=$cmd" <= 100 ? im${i}b1 : im$((i+1))b1" ; done
    # Execute band math
    otbcli_BandMath -progress true -il ${productList[@]} -out "$tmpFn" uint8 -exp "$cmd"
    # Apply color table to composite
    otbcli_ColorMapping -progress true -in "$tmpFn" -out "$outputFn""?&gdal:co:COMPRESS=DEFLATE" uint8 -method.custom.lut "/work/OT/siaa/Theia/hpc_scripts/LIS_SEB_style_OTB.txt"
    # Delete temporary file
    rm "$tmpFn"
fi
