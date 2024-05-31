#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

# Define label for output snow product
LABEL_NO_SNOW = "0"
LABEL_SNOW = "100"
LABEL_CLOUD = "205"
LABEL_NO_DATA = "255"

N_SWIR = 1
N_RED = 2
N_GREEN = 3
N_BLUE = 4
N_NIR = 5

GREEN = "green"
RED = "red"
SWIR = "swir"
BLUE = "blue"
NIR = "nir"

MODE_LASRC = 'lasrc'
MODE_SEN2COR = 'sen2cor'
MODE_SENTINEL2 = 'sentinel2'

MISSION_S2 = "S2"
MISSION_L8 = "L8"
MISSION_T5 = "T5"

# snow product mission name
SENTINEL2 = "SENTINEL2"
LIS = "LIS"
LANDSAT8_OLITIRS_XS = "LANDSAT8-OLITIRS-XS"
LANDSAT8 = "LANDSAT8"
N2A = "N2A"
FSC = "FSC"

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

# Filenames
TMP_DIR = "tmp"
LOG_FILE = "lis.log"
SLOPE_MASK = "slope_mask.tif"
BLUE_BAND_EXTRACTED = "blue_band_extracted.tif"
GREEN_BAND_EXTRACTED = "green_band_extracted.tif"
RED_BAND_EXTRACTED = "red_band_extracted.tif"
NIR_BAND_EXTRACTED = "nir_band_extracted.tif"
SWIR_BAND_EXTRACTED = "swir_band_extracted.tif"
BAND_EXTRACTED = "_band_extracted.tif"
BLUE_BAND_RESAMPLED = "blue_band_resampled.tif"
GREEN_BAND_RESAMPLED = "green_band_resampled.tif"
RED_BAND_RESAMPLED = "red_band_resampled.tif"
NIR_BAND_RESAMPLED = "nir_band_resampled.tif"
SWIR_BAND_RESAMPLED = "swir_band_resampled.tif"
BAND_RESAMPLED = "_band_resampled.tif"

DEM_RESAMPLED = "dem_resampled.tif"

IMG_VRT = "lis.vrt"
NO_DATA_MASK = "no_data_mask.tif"

RED_BAND = "red.tif"
RED_COARSE = "red_coarse.tif"
RED_NN = "red_nn.tif"

ALL_CLOUD_MASK = "all_cloud_mask.tif"
SHADOW_MASK = "shadow_mask.tif"
SHADOW_IN_MASK = "shadow_in_mask.tif"
SHADOW_OUT_MASK = "shadow_out_mask.tif"
HIGH_CLOUD_MASK = "high_cloud_mask.tif"
MASK_BACK_TO_CLOUD = "mask_back_to_cloud.tif"

SNOW_PASS1 = "snow_pass1.tif"
CLOUD_PASS1 = "cloud_pass1.tif"

SNOW_PASS2 = "snow_pass2.tif"
SNOW_PASS2_VEC = "snow_pass2_vec.shp"
SNOW_PASS3 = "snow_pass3.tif"
SNOW_PASS3_VEC = "snow_pass3_vec.shp"

AZIMUTH_PATH = "projection_azimuth.tif"
ZENITH_PATH = "projection_zenith.tif"
HILLSHADE_MASK = "hillshade_mask.tif"
SHADED_SNOW = "shaded_snow.tif"
UNCALIBRATED_SHADED_SNOW = "uncalibrated_shaded_snow.tif"

CLOUD_REFINE = "cloud_refine.tif"

SNOW_ALL = "LIS_SNOW_ALL.TIF"
SNOW_MASK = "LIS_SEB.TIF"
SNOW_VEC = "LIS_SEB_VEC.shp"
HISTOGRAM = "LIS_HISTO.TXT"
METADATA = "LIS_METADATA.XML"
NDSI = "LIS_NDSI.TIF"
FSCTOC = "LIS_FSCTOC.TIF"
FSCTOCHS = "LIS_FSCTOCHS.TIF"
FSCOG = "LIS_FSCOG.TIF"
FSCCLD = "LIS_CLD.tif"
QCFLAGS = "LIS_FSC_QCFLAGS.tif"
QCTOC = "LIS_FSC_QCTOC.tif"
QCOG = "LIS_FSC_QCOG.tif"

OUTPUT_DATES_FILE = "output_dates.txt"
# Error codes
INPUT_PARAMETER_ERROR = 2
UNKNOWN_PRODUCT_EXCEPTION = 3
CONFIGURATION_ERROR = 4
UNKNOWN_PLATFORM = 5
NO_PRODUCT_MATCHING_SYNTHESIS = 6
NO_SNOW_PRODUCT_FOUND = 7
NO_ZIP_FOUND = 8
OUTPUT_UNDEFINED = 9

# Date Time format
MUSCATE_DATETIME_FORMAT = "%Y%m%d-%H%M%S-%f"
LANDSAT_DATETIME_FORMAT = "%Y%m%d"
LIS_DATETIME_FORMAT = "%Y%m%dT%H%M%S"

# DOI
DOI_URL = "https://doi.org/10.24400/329360/F7Q52MNK"
