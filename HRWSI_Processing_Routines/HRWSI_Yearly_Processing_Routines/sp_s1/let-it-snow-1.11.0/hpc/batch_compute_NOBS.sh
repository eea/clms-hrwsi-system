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

#PBS -N TheiaNeige
#PBS -J 1-191:1
#PBS -l select=1:ncpus=1:mem=20000mb
#PBS -l walltime=00:59:00
#PBS -M gascoins@cesbio.cnes.fr
#PBS -m e

# Load lis environnment 
module load lis/develop

# Load all the available product names from the tile directory
pin=/work/OT/siaa/Theia/Neige/SNOW_ANNUAL_MAP_LIS_1.5/S2_with_L8_Densification/
inputFiles=($(find $pin -name multitemp_cloud_mask.vrt))

# use the PBS_ARRAY_INDEX variable to distribute jobs in parallel (bash indexing is zero-based)
i="${inputFiles[${PBS_ARRAY_INDEX} - 1]}"

# run script
python "${PBS_O_WORKDIR}"/compute_NOBS.py ${i}
