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

# script to make the TCD input file for FSC in LIS
# usage: sh makeTCDforLIS.sh T32TLS
tile=$1
echo "Prepare TCD to run LIS on tile ${tile}"
tcdFolder="/work/OT/siaa/Theia/Neige/CoSIMS/data/TCD/"
# prepare VRT from all TCD files (can be skipped when the VRT will be populated with all EEA tiles)
gdalbuildvrt $tcdFolder/TCD_2015_020m_eu_03035_d05.vrt $tcdFolder/TCD_2015_020m_eu_03035_d05*/TCD_2015_020m_eu_03035_d05*.tif
# use metadata from the DEM of the target tile to define the projection and extent
dem="/work/OT/siaa/Theia/Neige/DEM/S2__TEST_AUX_REFDE2_${tile}_0001.DBL.DIR/S2__TEST_AUX_REFDE2_${tile}_0001_ALT_R2.TIF"
proj=$(gdalsrsinfo -o proj4 $dem)
gdalinfo $dem -json > tmp.json
te=$(python2.7 -c "import json; print '{} {} {} {}'.format(*[item for sublist in [json.load(open('tmp.json'))['cornerCoordinates'][x] for x in ['lowerLeft','upperRight']] for item in sublist])")
eval gdalwarp -te $te -t_srs "${proj}" -tr 20 20 -r cubic $tcdFolder/TCD_2015_020m_eu_03035_d05.vrt $tcdFolder/TCD_2015_R2_${tile}.TIF
