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

from s2snow.otb_wrappers import compute_cloud_mask, band_math
from s2snow.lis_constant import MODE_LASRC, MODE_SEN2COR, GDAL_OPT, ALL_CLOUD_MASK, SHADOW_MASK, HIGH_CLOUD_MASK, \
    MASK_BACK_TO_CLOUD, SHADOW_IN_MASK, SHADOW_OUT_MASK, CLOUD_REFINE, MODE_SENTINEL2


def extract_all_clouds(cloud_mask, output_dir, all_cloud_mask=1, mode=MODE_SENTINEL2, ram=512):
    '''
    Extract all clouds from cloud mask.
    :param cloud_mask: input cloud mask
    :param output_dir: output directory
    :param all_cloud_mask: cloud condition for lasrc mode
    :param mode: sen2cor, lasrc or ""
    :param ram: default value is 512
    :return: all_cloud_mask_file
    '''
    logging.debug("Start extract_all_clouds.")
    logging.debug("cloud_mask : " + cloud_mask)
    logging.debug("all_cloud_mask : " + str(all_cloud_mask))
    logging.debug("mode : " + mode)
    logging.debug("ram : " + str(ram))

    all_cloud_mask_file = op.join(output_dir, ALL_CLOUD_MASK)
    logging.debug("all_cloud_mask_file : " + all_cloud_mask_file)

    if mode == MODE_LASRC:
        # Extract shadow which corresponds to  all cloud shadows in larsc product
        logging.info("lasrc mode -> extract all clouds from LASRC product using ComputeCloudMask application...")
        compute_cloud_mask(cloud_mask, all_cloud_mask_file + GDAL_OPT, str(all_cloud_mask), ram)
    else:
        if mode == MODE_SEN2COR:
            logging.debug("sen2cor mode -> extract all clouds from SCL layer...")
            logging.debug("All clouds in sen2cor SCL layer corresponds to:")
            logging.debug("- label == 3 -> Cloud shadows")
            logging.debug("- label == 8 -> Cloud medium probability")
            logging.debug("- label == 9 -> Cloud high probability")
            logging.debug("- label == 10 -> Thin cirrus")
            condition_all_clouds = "im1b1==3 || im1b1==8 || im1b1==9 || im1b1==10"
        else:
            condition_all_clouds = "im1b1 > 0"
        logging.debug("condition_all_clouds : " + condition_all_clouds)
        band_math([cloud_mask], all_cloud_mask_file + GDAL_OPT, "(" + condition_all_clouds + " > 0)?1:0", ram)
    logging.debug("End extract_all_clouds... : ")
    return all_cloud_mask_file


def extract_cloud_shadows(cloud_mask, output_dir, mode="", shadow_in_mask=32,
                          shadow_out_mask=64, ram=512):
    logging.debug("Start extract_cloud_shadows.")
    logging.debug("cloud_mask : " + cloud_mask)
    logging.debug("mode : " + mode)
    logging.debug("shadow_in_mask : " + str(shadow_in_mask))
    logging.debug("shadow_out_mask : " + str(shadow_out_mask))
    logging.debug("ram : " + str(ram))

    shadow_mask_file = op.join(output_dir, SHADOW_MASK)
    logging.debug("shadow_mask_file : " + shadow_mask_file)

    # Extract shadow masks differently if sen2cor or MAJA
    if mode == MODE_SEN2COR:
        logging.debug("sen2cor mode -> extract all clouds from SCL layer...")
        logging.debug("- label == 3 -> Cloud shadows")
        band_math([cloud_mask], shadow_mask_file + GDAL_OPT, "(im1b1 == 3)", ram)
    else:
        shadow_in_mask_file = op.join(output_dir, SHADOW_IN_MASK)
        logging.debug("shadow_in_mask_file : " + shadow_in_mask_file)
        shadow_out_mask_file = op.join(output_dir, SHADOW_OUT_MASK)
        logging.debug("shadow_out_mask_file : " + shadow_out_mask_file)

        # First extract shadow wich corresponds to shadow of clouds inside the
        # image
        compute_cloud_mask(cloud_mask, shadow_in_mask_file + GDAL_OPT, str(shadow_in_mask), ram)

        # Then extract shadow mask of shadows from clouds outside the image
        compute_cloud_mask(cloud_mask, shadow_out_mask_file + GDAL_OPT, str(shadow_out_mask), ram )

        # The output shadow mask corresponds to a OR logic between the 2 shadow masks
        band_math([shadow_in_mask_file, shadow_out_mask_file], shadow_mask_file + GDAL_OPT,
                  "(im1b1 == 1) || (im2b1 == 1)", ram)

    return shadow_mask_file


def extract_high_clouds(cloud_mask_file, output_dir, high_cloud_mask=128, mode="", ram=512):
    logging.debug("Start extract_high_clouds.")
    logging.debug("cloud_mask_file : " + cloud_mask_file)
    logging.debug("high_cloud_mask : " + str(high_cloud_mask))
    logging.debug("mode : " + mode)
    logging.debug("ram : " + str(ram))

    high_cloud_mask_file = op.join(output_dir, HIGH_CLOUD_MASK)
    logging.debug("high_cloud_mask_file : " + high_cloud_mask_file)

    if mode == 'sen2cor':
        logging.debug("sen2cor mode -> extract all clouds from SCL layer...")
        logging.debug("- label == 10 -> Thin cirrus")
        band_math([cloud_mask_file], high_cloud_mask_file + GDAL_OPT, "(im1b1 == 10)", ram)
    else:
        compute_cloud_mask(cloud_mask_file, high_cloud_mask_file + GDAL_OPT, str(high_cloud_mask), ram)

    return high_cloud_mask_file


def extract_back_to_cloud_mask(cloud_mask_file, red_band_file, output_dir, red_back_to_cloud=100, mode="", ram=512):
    logging.debug("Start extract_back_to_cloud_mask.")
    logging.debug("cloud_mask_file : " + cloud_mask_file)
    logging.debug("red_band_file : " + red_band_file)
    logging.debug("output_dir : " + output_dir)
    logging.debug("red_back_to_cloud : " + str(red_back_to_cloud))
    logging.debug("mode : " + mode)
    logging.debug("ram : " + str(ram))

    mask_back_to_cloud_file = op.join(output_dir, MASK_BACK_TO_CLOUD)
    logging.debug("mask_back_to_cloud_file : " + mask_back_to_cloud_file)

    if mode == MODE_SEN2COR:
        logging.debug("sen2cor mode -> extract all clouds from SCL layer...")
        logging.debug("All clouds in sen2cor SCL layer corresponds to:")
        logging.debug("- label == 3 -> Cloud shadows")
        logging.debug("- label == 8 -> Cloud medium probability")
        logging.debug("- label == 9 -> Cloud high probability")
        logging.debug("- label == 10 -> Thin cirrus")
        condition_all_clouds = "im1b1==3 || im1b1==8 || im1b1==9 || im1b1==10"
    else:
        condition_all_clouds = "im1b1 > 0"

    condition_back_to_cloud = "(" + condition_all_clouds + ") and (im2b1 > " + str(red_back_to_cloud) + ")"
    logging.debug("condition_back_to_cloud : " + condition_back_to_cloud)

    band_math([cloud_mask_file, red_band_file], mask_back_to_cloud_file + GDAL_OPT, condition_back_to_cloud + "?1:0",
              ram)

    return mask_back_to_cloud_file


def refine_cloud_mask(all_cloud_mask_file, shadow_mask_file, red_nn_file, high_cloud_mask_file, cloud_pass1_file,
                      output_dir, red_dark_cloud = 300, ram=512):
    """
    Refine cloud mask
    :param all_cloud_mask_file: all cloud mask
    :param shadow_mask_file: shadow mask file
    :param red_nn_file: red nn file
    :param high_cloud_mask_file: high cloud mask
    :param cloud_pass1_file: cloud mask from pass 1
    :param output_dir: output directory
    :param red_dark_cloud: red dark cloud default is 300
    :param ram: ram for otb call defautl is 512
    :return: Refined cloud mask
    """
    logging.debug("Refine cloud mask")
    logging.debug("all_cloud_mask_file : " + all_cloud_mask_file)
    logging.debug("shadow_mask_file : " + shadow_mask_file)
    logging.debug("red_nn_file : " + red_nn_file)
    logging.debug("high_cloud_mask_file : " + high_cloud_mask_file)
    logging.debug("cloud_pass1_file : " + cloud_pass1_file)
    logging.debug("output_dir : " + output_dir)
    logging.debug("red_dark_cloud : " + str(red_dark_cloud))
    logging.debug("ram : " + str(ram))

    condition_cloud2 = "im3b1>" + str(red_dark_cloud)
    logging.debug("condition_cloud2 : " + condition_cloud2)

    # this condition check if pass1_5 caused a cloud mask update
    condition_donuts = "(im1b1!=im5b1)"
    logging.debug("condition_donuts : " + condition_donuts)

    condition_shadow = "((im1b1==1 and " + condition_cloud2 + \
                       ") or im2b1==1 or im4b1==1 or " + condition_donuts + ")"
    logging.debug("condition_shadow : " + condition_shadow)

    cloud_refine_file = op.join(output_dir, CLOUD_REFINE)
    logging.info("Refine cloud file: " + cloud_refine_file)

    band_math([all_cloud_mask_file, shadow_mask_file, red_nn_file, high_cloud_mask_file,
               cloud_pass1_file], cloud_refine_file + GDAL_OPT, condition_shadow, ram)

    return cloud_refine_file
