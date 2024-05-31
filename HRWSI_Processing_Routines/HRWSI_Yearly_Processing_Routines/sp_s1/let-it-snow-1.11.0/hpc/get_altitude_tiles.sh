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

p="/work/OT/muscate/prod/muscate_prod/data_production/dataref/"
echo "Tile Mean_Altitude_Over_L2_Coverage Altitude_Standard_Deviation_Over_L2_Coverage" > Altitude_Over_L2_Coverage.txt
for i in `ls -d $p/S2__TEST_AUX_REFDE2_T*`
do
t=`basename $i | cut -d_ -f6`
ma=`grep -i Mean_Altitude_Over_L2_Coverage $p/S2*$t*/S2*$t*/S2*$t*.HDR | cut -d\> -f2 | cut -d\< -f1 `
as=`grep -i Altitude_Standard_Deviation_Over_L2_Coverage $p/S2*$t*/S2*$t*/S2*$t*.HDR | cut -d\> -f2 | cut -d\< -f1 `
echo $t $ma $as >> Altitude_Over_L2_Coverage.txt
done
