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
import re
from datetime import datetime
import logging
import os
import os.path as op
import zipfile
from os.path import basename, dirname

from s2snow.lis_constant import SENTINEL2, LIS, LANDSAT8_OLITIRS_XS, LANDSAT8, N2A, MUSCATE_DATETIME_FORMAT, LIS_DATETIME_FORMAT, LANDSAT_DATETIME_FORMAT, FSC
from s2snow.utils import find_file
from s2snow.lis_exception import UnknownPlatform, NoSnowProductFound, NoZipFound


class SnowProduct:
    def __init__(self, absolute_filename, tmp):
        # example 1 "SENTINEL2A_20160912-103551-370_L2B-SNOW_T32TLS_D_V1-0"
        # example 2 "LANDSAT8_OLITIRS_XS_20160812_N2A_France-MetropoleD0005H0001"
        # exemple 3 : "LIS_S2-SNOW-FSC_T31TCH_20180101T105435_1.7.0_1"
        # exemple 4 : "FSC_20200612T110855_S2A_T31TCJ_V100_1[.zip]"

        logging.debug("snow_product initialisation")
        logging.debug("absolute_filename : " + absolute_filename)

        self.product_name = basename(absolute_filename)
        logging.debug("product_name : " + self.product_name)
        self.acquisition_date = None
        self.tile_id = None
        self.snow_mask = None
        self.metadata_file = None

        self.product_path = absolute_filename
        name_splitted = self.product_name.split("_")
        platform = name_splitted[0]
        logging.debug("platform : " + platform)

        # unzip input if zipped
        zip_product = absolute_filename.lower().endswith('.zip')
        zip_file = None
        if not zip_product:
            for root, dirs, files in os.walk(absolute_filename):
                for file in files:
                    if file.lower().endswith('.zip'):
                        zip_file = file
                        break
        else:
            zip_file = absolute_filename

        if zip_file is not None:
            logging.debug("zipfile : " + op.join(absolute_filename, zip_file))
            logging.info("The snow product is stored in a zip, extracting zip file.")
            extract_snow_mask(op.join(absolute_filename, zip_file), tmp)
            # self.product_path = op.join(tmp, op.basename(op.splitext(zip_file)[0]))
            self.product_path = tmp
            logging.debug("product_path : " + self.product_path)

        if SENTINEL2 in platform:
            logging.debug("SENTINEL2 case")
            self.acquisition_date = datetime.strptime(name_splitted[1], MUSCATE_DATETIME_FORMAT)
            self.tile_id = name_splitted[3]
            self.snow_mask = find_file(self.product_path, ".*_SNW_R2.(tif|TIF)")
            self.metadata_file = find_file(self.product_path, ".*_MTD_ALL.(xml|XML)")

            if self.snow_mask is None:
                logging.debug("sentinel2 case with lis case :)")
                self.snow_mask = find_file(self.product_path, ".*SNOW-FSC_.*(tif|TIF)")
                self.metadata_file = find_file(self.product_path, ".*SNOW-.*(xml|XML)")

        elif LANDSAT8_OLITIRS_XS == platform:
            logging.debug("LANDSAT8_OLITIRS_XS case")
            self.acquisition_date = datetime.strptime(name_splitted[1], MUSCATE_DATETIME_FORMAT)
            self.tile_id = name_splitted[3]
            self.snow_mask = find_file(self.product_path, ".*_SNW_XS.(tif|TIF)")
            if self.snow_mask is None:
                self.snow_mask = find_file(self.product_path, ".*SNOW-MSK_.*(tif|TIF)")
            self.metadata_file = find_file(self.product_path, ".*_MTD_ALL.(xml|XML)")
        elif LANDSAT8 in platform and N2A in self.product_name:
            logging.debug("LANDSAT8 case")
            self.acquisition_date = datetime.strptime(name_splitted[3], LANDSAT_DATETIME_FORMAT)
            self.tile_id = name_splitted[5]
            self.snow_mask = find_file(self.product_path, ".*_SNW_XS.(tif|TIF)")
            if self.snow_mask is None:
                self.snow_mask = find_file(self.product_path, ".*SNOW-MSK_.*(tif|TIF)")
            self.metadata_file = find_file(self.product_path, ".*_MTD_ALL.(xml|XML)")
        elif LIS in platform:
            logging.debug("LIS case")
            self.acquisition_date = datetime.strptime(name_splitted[3], LIS_DATETIME_FORMAT)
            self.tile_id = name_splitted[2]
            self.snow_mask = find_file(self.product_path, ".*SNOW-FS.*C_.*(tif|TIF)")
            self.metadata_file = find_file(self.product_path, ".*SNOW-.*.(xml|XML)")
        elif FSC in platform:
            logging.debug("FSC case")
            self.acquisition_date = datetime.strptime(name_splitted[1], LIS_DATETIME_FORMAT)
            self.tile_id = name_splitted[3]
            self.snow_mask = find_file(self.product_path, ".*FSC(OG|TOC).(tif|TIF)")
            self.metadata_file = find_file(self.product_path, ".*_MTD.(xml|XML)")
        else:
            msg = "Unknown platform or producer: " + platform
            logging.error(msg)
            raise UnknownPlatform(msg)

        if self.snow_mask is None:
            logging.debug("looking for LIS_SEB product")
            self.snow_mask = find_file(self.product_path, "LIS_SEB")

        if self.metadata_file is None:
            self.metadata_file = find_file(self.product_path, "LIS_METADATA.XML")

        self.log_product()

    def __repr__(self):
        return op.join(self.product_path)

    def __str__(self):
        return op.join(self.product_path)

    def log_product(self):
        logging.debug("-------------------------------------")
        logging.debug("SNOW PRODUCT")
        logging.debug("-------------------------------------")
        logging.debug("product_name : " + self.product_name)
        logging.debug("acquisition_date : " + str(self.acquisition_date))
        logging.debug("tile_id : " + self.tile_id)
        logging.debug("snow_mask : " + str(self.get_snow_mask()))
        if self.metadata_file:
            logging.debug("metadata_file : " + str(self.metadata_file))

    def get_snow_mask(self):
        if self.snow_mask and op.exists(self.snow_mask):
            return self.snow_mask
        else:
            msg = "The snow mask has not been found."
            logging.error(msg)
            raise NoSnowProductFound(msg)

    def get_metadata(self):
        if self.metadata_file and op.exists(self.metadata_file):
            return self.metadata_file
        else:
            logging.warning("The metadata file has not been found.")


def extract_from_zipfile(file_name, output_folder):
    """ Extract from the zip file all files corresponding
    to one of the provided patterns
    """
    zip_input = zipfile.ZipFile(file_name)
    zip_input.extractall(path=output_folder)


def extract_snow_mask(zip_file, output_folder):
    if op.exists(zip_file):
        extract_from_zipfile(zip_file, output_folder)
    else:
        msg = "Extraction failed - zipfile does not exist : " + zip_file
        logging.error(msg)
        raise NoZipFound(msg)
