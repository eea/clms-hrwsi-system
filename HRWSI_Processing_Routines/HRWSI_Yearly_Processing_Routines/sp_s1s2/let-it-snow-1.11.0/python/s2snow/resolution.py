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
import logging
import os.path as op
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from s2snow.lis_constant import BAND_RESAMPLED


def define_band_resolution(band):
    """
    Define band resolution
    :param band: input band
    :return: band resolution
    """
    logging.debug("Define resolution for band : " + band)

    dataset = gdal.Open(band, GA_ReadOnly)
    resolution = dataset.GetGeoTransform()[1]

    return resolution


def adapt_to_target_resolution(band_name, resolution, target_resolution, band_extracted_file, output_dir):
    """
    Adapt band to target resolution
    :param band_name: RED, GREEN or SWIR
    :param resolution: band resolution
    :param target_resolution: target resolution
    :param band_extracted_file: input band file
    :param output_dir: output directory
    :return: band resampled to target resolution or input band if band resolution is already target resolution
    """
    logging.debug("Adapt band to target.")
    if resolution != target_resolution:
        logging.debug("Change band resolution to : " + str(target_resolution) + " meters.")
        logging.debug("band_name : " + band_name)
        logging.debug("resolution : " + str(resolution))
        logging.debug("target_resolution : " + str(target_resolution))
        logging.debug("band_extracted_file : " + band_extracted_file)
        band_resampled_file = op.join(output_dir, band_name + BAND_RESAMPLED)
        logging.info(band_name + "_band_resampled_file : " + band_resampled_file)
        
        gdal.Warp(
                band_resampled_file,
                band_extracted_file,
                resampleAlg=gdal.GRIORA_Cubic,
                xRes=target_resolution,
                yRes=target_resolution)
    else:
        logging.info("Band resolution is already target resolution : " + str(target_resolution))
        band_resampled_file = band_extracted_file
    return band_resampled_file


