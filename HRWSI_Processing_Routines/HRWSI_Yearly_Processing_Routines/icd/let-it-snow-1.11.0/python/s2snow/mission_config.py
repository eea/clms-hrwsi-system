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

MAJA_parameters = {"multi": 10,
                   "green_band": ".*FRE_R1.DBL.TIF$",
                   "green_band_number": 2,
                   "red_band": ".*FRE_R1.DBL.TIF$",
                   "red_band_number": 3,
                   "swir_band": ".*FRE_R2.DBL.TIF$",
                   "swir_band_number": 5,
                   "cloud_mask": ".*CLD_R2.DBL.TIF$",
                   "dem": ".*ALT_R2\.TIF$",
                   "shadow_in_mask": 4,
                   "shadow_out_mask": 8,
                   "all_cloud_mask": 1,
                   "high_cloud_mask": 128,
                   "resize_factor": 12}

SEN2COR_parameters = {"mode": "sen2cor",
                      "multi": 10,
                      "green_band": ".*_B03_10m.jp2$",
                      "green_band_number": 1,
                      "red_band": ".*_B04_10m.jp2$",
                      "red_band_number": 1,
                      "swir_band": ".*_B11_20m.jp2$",
                      "swir_band_number": 1,
                      "cloud_mask": ".*_SCL_20m.jp2$",
                      "dem": "",
                      "shadow_in_mask": 3,
                      "shadow_out_mask": 3,
                      "all_cloud_mask": 8,
                      "high_cloud_mask": 10,
                      "resize_factor": 12}

Take5_parameters = {"multi": 1,
                    "green_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                    "green_band_number": 1,
                    "red_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                    "red_band_number": 2,
                    "swir_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                    "swir_band_number": 4,
                    "cloud_mask": ".*NUA.*\.TIF$",
                    "div_mask": ".*DIV.*\.TIF$",
                    "div_slope_threshold": 8,
                    "dem": ".*\.tif",
                    "shadow_in_mask": 64,
                    "shadow_out_mask": 128,
                    "all_cloud_mask": 1,
                    "high_cloud_mask": 32,
                    "resize_factor": 8}

S2_parameters = {"multi": 10,
                 "green_band": ".*FRE_B3.*\.tif$",
                 "green_band_number": 1,
                 "red_band": ".*FRE_B4.*\.tif$",
                 "red_band_number": 1,
                 "blue_band": ".*SRE_B2.*\.tif$",
                 "blue_band_number": 1,
                 "nir_band": ".*SRE_B8A.*\.tif$",
                 "nir_band_number": 1,
                 "swir_band": ".*FRE_B11.*\.tif$",
                 "swir_band_number": 1,
                 "cloud_mask": ".*CLM_R2.*\.tif$",
                 "dem": ".*ALT_R2\.TIF$",
                 "div_mask": ".*MG2_R2.*\.tif$",
                 "div_slope_threshold": 64,
                 "shadow_in_mask": 32,
                 "shadow_out_mask": 64,
                 "all_cloud_mask": 1,
                 "high_cloud_mask": 128,
                 "resize_factor": 12,
                 "metadata": ".*MTD_ALL.*\.xml$"
                 }

L8_parameters_new_format = {"multi": 1,
                            "green_band": ".*FRE_B3.*\.tif$",
                            "green_band_number": 1,
                            "red_band": ".*FRE_B4.*\.tif$",
                            "red_band_number": 1,
                            "swir_band": ".*FRE_B6.*\.tif$",
                            "swir_band_number": 1,
                            "blue_band": ".*SRE_B2.*\.tif$",
                            "blue_band_number": 1,
                            "nir_band": ".*SRE_B5.*\.tif$",
                            "nir_band_number": 1,
                            "cloud_mask": ".*CLM_XS.*\.tif$",
                            "dem": ".*ALT_R2\.TIF$",
                            "div_mask": ".*MG2_XS.*\.tif$",
                            "div_slope_threshold": 64,
                            "shadow_in_mask": 32,
                            "shadow_out_mask": 64,
                            "all_cloud_mask": 1,
                            "high_cloud_mask": 128,
                            "resize_factor": 8,
                            "metadata": ".*MTD_ALL.*\.xml$" }

L8_parameters = {"multi": 1,
                 "green_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                 "green_band_number": 3,
                 "red_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                 "red_band_number": 4,
                 "swir_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                 "swir_band_number": 6,
                 "blue_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                 "blue_band_number": 2,
                 "nir_band": ".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                 "nir_band_number": 5,
                 "cloud_mask": ".*NUA.*\.TIF$",
                 "div_mask": ".*DIV.*\.TIF$",
                 "div_slope_threshold": 8,
                 "dem": ".*\.tif",
                 "shadow_in_mask": 64,
                 "shadow_out_mask": 128,
                 "all_cloud_mask": 1,
                 "high_cloud_mask": 32,
                 "resize_factor": 8,
                 "metadata": ".*MTD_ALL.*\.xml$"}

LANDSAT8_LASRC_parameters = {"mode": "lasrc",
                             "multi": 10,
                             "green_band": ".*_sr_band3.tif$",
                             "green_band_number": 1,
                             "red_band": ".*_sr_band4.tif$",
                             "red_band_number": 1,
                             "swir_band": ".*_sr_band6.tif$",
                             "swir_band_number": 1,
                             "cloud_mask": ".*_pixel_qa.tif$",
                             "dem": ".*\.tif",
                             "shadow_in_mask": 8,
                             "shadow_out_mask": 8,
                             "all_cloud_mask": 224,  # cloud with high confidence (32+(64+128))
                             "high_cloud_mask": 800,  # cloud and high cloud with high confidence (32 + (512+256))
                             "resize_factor": 8}

mission_parameters = {"S2": S2_parameters, \
                      "LANDSAT8": L8_parameters, \
                      "LANDSAT8_new_format": L8_parameters_new_format, \
                      "Take5": Take5_parameters, \
                      "MAJA": MAJA_parameters, \
                      "SEN2COR": SEN2COR_parameters, \
                      "LANDSAT8_LASRC": LANDSAT8_LASRC_parameters
                      }