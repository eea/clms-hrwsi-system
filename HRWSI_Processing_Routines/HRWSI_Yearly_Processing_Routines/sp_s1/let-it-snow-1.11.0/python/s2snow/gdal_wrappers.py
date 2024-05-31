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
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GA_Update

from s2snow.lis_constant import BAND_EXTRACTED, RED_BAND, RED_NN, RED_COARSE, IMG_VRT, N_RED


def extract_band(band_name, band_path, no_band, output_dir, no_data = -1000):
    '''
    Extract band from band_path
    :param band_name: BLUE, GREEN, RED, NIR or SWIR
    :param band_path: path to access band
    :param no_band: band numero to extract
    :param output_dir: output directory
    :param no_data: no_data value - default = -1000
    :return: the extracted band file as GTiff
    '''
    logging.debug("Extract band")
    logging.debug("band_name : " + band_name)
    logging.debug("band_path : " + band_path)
    logging.debug("no_band : " + str(no_band))
    logging.debug("output_dir : " + output_dir)
    logging.debug("no_data : " + str(no_data))

    extracted_band_file = op.join(output_dir, band_name + BAND_EXTRACTED)
    logging.info("Extract band " + extracted_band_file)
    ("GDAL_NUM_THREADS", "ALL_CPUS")
    gdal.Translate(extracted_band_file, band_path, format='GTiff',
                   outputType=gdal.GDT_Int16, noData=no_data, bandList=[no_band])

    return extracted_band_file


def extract_red_band(img_vrt, output_dir, no_data=-10000):
    '''
    Extract red band from vrt image.
    :param img_vrt: input vrt image
    :param output_dir: output directory
    :param no_data: no_data value - default value = -10000
    :return: extracted red band file
    '''
    logging.debug("Extract red band")
    logging.debug("img_vrt : " + img_vrt)
    logging.debug("output_dir : " + output_dir)
    logging.debug("no_data : " + str(no_data))

    red_band_file = op.join(output_dir, RED_BAND)
    logging.info("Extract red band file from vrt : " + red_band_file)

    
    gdal.Translate(red_band_file, img_vrt, format='GTiff', outputType=gdal.GDT_Int16, noData=no_data, bandList=[N_RED])
    return red_band_file


def resample_red_band(red_band, output_dir, xSize, ySize, resize_factor=12):
    '''
    Resample red band using multiresolution pyramid
    :param red_band: input red band
    :param output_dir: output directory
    :param xSize: dataset xsize
    :param ySize: dataset ysize
    :param resize_factor: resize_factor - default 12
    :return: resampled red band file
    '''
    logging.debug("Resample red band using multiresolution pyramid")
    logging.debug("red_band : " + red_band)
    logging.debug("output_dir : " + output_dir)
    logging.debug("xSize : " + str(xSize))
    logging.debug("ySize : " + str(ySize))
    logging.debug("resize_factor : " + str(resize_factor))

    red_coarse_file = op.join(output_dir, RED_COARSE)
    logging.info("Resample red band using multiresolution pyramid : " + red_coarse_file)

    
    gdal.Warp(red_coarse_file, red_band, resampleAlg=gdal.GRIORA_Bilinear, width=xSize / resize_factor,
              height=ySize / resize_factor)

    return red_coarse_file


def resample_red_band_nn(red_coarse_file, output_dir, xSize, ySize):
    '''
    Resample red band nn
    :param red_coarse_file: input red coarse file
    :param output_dir:  output directory
    :param xSize: dataset xsize
    :param ySize: dataset ysizz
    :return: red band nn
    '''
    logging.debug("Resample red band nn")
    logging.debug("red_coarse : " + red_coarse_file)
    logging.debug("xSize : " + str(xSize))
    logging.debug("ySize : " + str(ySize))

    red_nn_file = op.join(output_dir, RED_NN)
    logging.info("Resample red band nn  : " + red_nn_file)

    
    gdal.Warp(red_nn_file, red_coarse_file, resampleAlg=gdal.GRIORA_NearestNeighbour, width=xSize, height=ySize)

    return red_nn_file


def extract_red_nn(red_band_file, output_dir, resize_factor=12):
    '''
    Extract red nn band.
    :param red_band_file: input red band file
    :param output_dir: output directory
    :param resize_factor: resize factor - default = 12
    :return: red nn file
    '''
    logging.debug("Extract red nn")
    logging.debug("red_band_file : " + red_band_file)
    logging.debug("output_dir : " + output_dir)

    dataset = gdal.Open(red_band_file, GA_ReadOnly)
    xSize = dataset.RasterXSize
    ySize = dataset.RasterYSize

    # Get geotransform to retrieve resolution
    logging.debug("Retrieve geotransform")
    geotransform = dataset.GetGeoTransform()
    dataset = None

    # resample red band using multi-resolution pyramid
    red_coarse_file = resample_red_band(red_band_file, output_dir, xSize, ySize, resize_factor=resize_factor)

    # Resample red band nn
    red_nn_file = resample_red_band_nn(red_coarse_file, output_dir, xSize, ySize)

    # edit result to set the resolution to the input image resolution
    # TODO need to find a better solution and also guess the input spacing
    # (using maccs resampling filter)
    logging.debug("Set geotransform to red band nn.")
    dataset = gdal.Open(red_nn_file, gdal.GA_Update)
    dataset.SetGeoTransform(geotransform)
    dataset = None

    return red_nn_file


def update_cloud_mask(snow_mask, cloud_mask, snow_mask_init, cloud_mask_file):
    updated_cloud_mask = np.where((snow_mask == 0) & (snow_mask_init == 1), 1, cloud_mask)
    dataset = gdal.Open(cloud_mask_file, GA_Update)
    band = dataset.GetRasterBand(1)
    band.WriteArray(updated_cloud_mask)
    dataset = None


def update_snow_mask(snow_mask, snow_mask_file):
    dataset = gdal.Open(snow_mask_file, GA_Update)
    band = dataset.GetRasterBand(1)
    band.WriteArray(snow_mask)
    dataset = None


def initialize_vrt(swir_band_resampled, red_band_resampled, green_band_resampled, output_dir, blue_band_resampled=None, nir_band_resampled=None):
    """
    Initialize lis vrt with red, green and swit band
    :param swir_band_resampled: swir band (target resolution)
    :param red_band_resampled: red band (target resolution)
    :param green_band_resampled: green band (target resolution)
    :param output_dir: output directory
    :param blue_band_resampled: (optional) blue band (target resolution)
    :param nir_band_resampled: (optional) nir band (target resolution)
    :return: vrt composed by three input bands.
    """
    img_vrt = op.join(output_dir, IMG_VRT)
    logging.info("img_vrt : " + img_vrt)
    
    if blue_band_resampled is not None and nir_band_resampled is not None:
        gdal.BuildVRT(img_vrt, [swir_band_resampled, red_band_resampled, green_band_resampled, blue_band_resampled, nir_band_resampled], separate=True)
    else:
        gdal.BuildVRT(img_vrt, [swir_band_resampled, red_band_resampled, green_band_resampled], separate=True)
    return img_vrt
