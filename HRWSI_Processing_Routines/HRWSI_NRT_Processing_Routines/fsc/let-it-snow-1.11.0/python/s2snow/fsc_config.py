#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Centre National d'Etudes Spatiales (CNES)
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
import json
import logging
import os
import zipfile
import re

from s2snow.lis_constant import MODE_SENTINEL2, MISSION_S2, MISSION_L8, MISSION_T5
from s2snow.lis_exception import LisConfigurationException, UnknownProductException
from s2snow.mission_config import mission_parameters
from s2snow.utils import find_file

sentinel2Acronyms = ['S2', 'SENTINEL2', 'S2A', 'S2B']


class FscConfig:

    def __init__(self, data, input_dir, dem, tcd, water_mask, relief_shadow_mask=None):

        self.product_id = ""
        self.mission = MISSION_S2
        self.tile_id = None
        self.acquisition_date = None

        # general
        self.multi = 10
        self.mode = MODE_SENTINEL2
        self.nb_threads = 1
        self.no_data = -10000
        self.do_preprocessing = False
        self.ram = 512

        # vector
        self.generate_vector = True
        self.generate_intermediate_vectors = False
        self.use_gdal_trace_outline = True
        self.gdal_trace_outline_dp_toler = 0
        self.gdal_trace_outline_min_area = 0

        # cloud
        self.all_cloud_mask = 1
        self.high_cloud_mask = 128
        self.shadow_in_mask = 32
        self.shadow_out_mask = 64
        self.red_back_to_cloud = 100
        self.red_back_to_cloud *= self.multi
        self.resize_factor = 12
        self.red_dark_cloud = 300
        self.red_dark_cloud *= self.multi
        self.strict_cloud_mask = False
        self.rm_snow_inside_cloud = False
        self.dilation_radius = 5
        self.cloud_threshold = 0.85
        self.cloud_min_area_size = 25000

        # snow
        self.dz = 100
        self.ndsi_pass1 = 0.4
        self.red_pass1 = 200
        self.red_pass1 *= self.multi
        self.ndsi_pass2 = 0.15
        self.red_pass2 = 40
        self.red_pass2 *= self.multi
        self.fsnow_lim = 0.1
        self.fsnow_total_lim = 0.001
        self.fclear_lim = 0.1

        
        # shaded snow
        self.detect_shaded_snow = False
        self.relief_shadow_mask = None
        self.hillshade_lim = 0.2
        self.shaded_snow_pass = 160
        
        # fsc
        self.tcd_file = None
        self.fscOg_Eq = "fscToc/(1-tcd)"
        self.fscToc_Eq = "1.45*ndsi-0.01"

        # water mask
        self.water_mask_path = None
        self.water_mask_raster_values = [1]

        # input
        self.div_mask = None
        self.div_slope_threshold = None
        self.dem = None
        self.cloud_mask = None
        self.blue_band_no_band = 1
        self.blue_band_path = None
        self.green_band_no_band = 1
        self.green_band_path = None
        self.red_band_no_band = 1
        self.red_band_path = None
        self.nir_band_no_band = 1
        self.nir_band_path = None
        self.swir_band_no_band = 1
        self.swir_band_path = None
        self.metadata = None
        self.read_product(input_dir)
        self.load_config(data)
        self.update_dem(dem)
        self.update_tcd(tcd)
        self.update_water_mask(water_mask)
        self.update_relief_shadow_mask(relief_shadow_mask)
        self.log_configuration()

    def load_config(self, data):
        # ----------------------------------------------------------------------
        # General
        # ----------------------------------------------------------------------
        general = data.get("general", None)
        if general is not None:
            logging.info("Load general parameters")

            multi = general.get("multi", 10)  # Multiplier to handle S2 scaling
            if self.multi is None:
                self.multi = multi

            mode = general.get("mode", MODE_SENTINEL2)
            if self.mode is None:
                self.mode = mode

            self.nb_threads = general.get("nb_threads", 1)
            self.no_data = general.get("no_data", -10000)
            self.do_preprocessing = general.get("preprocessing", False)
            self.ram = general.get("ram", 512)

        else:
            logging.warning("general parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Vector
        # ----------------------------------------------------------------------
        vector = data.get("vector", None)
        if vector is not None:
            logging.info("Load vector parameters")

            self.generate_vector = vector.get("generate_vector", True)
            self.generate_intermediate_vectors = vector.get("generate_intermediate_vectors", False)
            self.use_gdal_trace_outline = vector.get("use_gdal_trace_outline", True)
            self.gdal_trace_outline_dp_toler = vector.get("gdal_trace_outline_dp_toler", 0)
            self.gdal_trace_outline_min_area = vector.get("gdal_trace_outline_min_area", 0)

        else:
            logging.warning("vector parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Cloud
        # ----------------------------------------------------------------------
        cloud = data.get("cloud", None)
        if cloud is not None:
            logging.info("Load cloud parameters")
            all_cloud_mask = cloud.get("all_cloud_mask", None)
            if all_cloud_mask is not None:
                self.all_cloud_mask = all_cloud_mask  # surcharge avec la valeur dans le fichier de configuration
            else:
                if self.all_cloud_mask is None:
                    self.all_cloud_mask = 1  # default value

            high_cloud_mask = cloud.get("high_cloud_mask", None)
            if high_cloud_mask is not None:
                self.high_cloud_mask = high_cloud_mask  # surcharge avec la valeur dans le fichier de configuration
            else:
                if self.high_cloud_mask is None:
                    self.high_cloud_mask = 128  # default value

            shadow_in_mask = cloud.get("shadow_in_mask", None)
            if shadow_in_mask is not None:
                self.shadow_in_mask = shadow_in_mask  # surcharge avec la valeur dans le fichier de configuration
            else:
                if self.shadow_in_mask is None:
                    self.shadow_in_mask = 32  # default value

            shadow_out_mask = cloud.get("shadow_out_mask", None)
            if shadow_out_mask is not None:
                self.shadow_out_mask = shadow_out_mask  # surcharge avec la valeur dans le fichier de configuration
            else:
                if self.shadow_out_mask is None:
                    self.shadow_out_mask = 64  # default value

            self.red_back_to_cloud = cloud.get("red_back_to_cloud", 100)
            self.red_back_to_cloud *= self.multi

            resize_factor = cloud.get("resize_factor", None)
            if resize_factor is not None:
                self.resize_factor = resize_factor  # surcharge avec la valeur dans le fichier de configuration
            else:
                if self.resize_factor is None:
                    self.resize_factor = 12  # default value

            self.red_dark_cloud = cloud.get("red_dark_cloud", 300)
            self.red_dark_cloud *= self.multi

            # Strict cloud mask usage (off by default)
            # If set to True no pixel from the cloud mask will be marked as snow
            self.strict_cloud_mask = cloud.get("strict_cloud_mask", False)

            # Suppress snow area surrounded by cloud (off by default)
            self.rm_snow_inside_cloud = cloud.get("rm_snow_inside_cloud", False)
            self.dilation_radius = cloud.get("rm_snow_inside_cloud_dilation_radius", 5)
            self.cloud_threshold = cloud.get("rm_snow_inside_cloud_threshold", 0.85)
            self.cloud_min_area_size = cloud.get("rm_snow_inside_cloud_min_area", 25000)

        else:
            logging.warning("cloud parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Snow
        # ----------------------------------------------------------------------
        snow = data.get("snow", None)
        if snow is not None:
            logging.info("Load snow parameters")

            self.dz = snow.get("dz", 100)
            self.ndsi_pass1 = snow.get("ndsi_pass1", 0.4)
            self.red_pass1 = snow.get("red_pass1", 200)
            self.red_pass1 *= self.multi
            self.ndsi_pass2 = snow.get("ndsi_pass2", 0.15)
            self.red_pass2 = snow.get("red_pass2", 40)
            self.red_pass2 *= self.multi
            self.fsnow_lim = snow.get("fsnow_lim", 0.1)
            self.fsnow_total_lim = snow.get("fsnow_total_lim", 0.001)
            self.fclear_lim = snow.get("fclear_lim", 0.1)

        else:
            logging.warning("snow parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Shaded snow
        # ----------------------------------------------------------------------
        shaded_snow = data.get("shaded_snow", None)
        if shaded_snow is not None:
            logging.info("Load shaded_snow parameters")

            self.detect_shaded_snow = shaded_snow.get("detect_shaded_snow", False)
            self.relief_shadow_mask = shaded_snow.get("relief_shadow_mask", None)
            self.hillshade_lim = shaded_snow.get("hillshade_lim", 0.2)
            self.shaded_snow_pass = shaded_snow.get("shaded_snow_pass", 160)
            self.rastertools_use = shaded_snow.get("rastertools_use", True)
            self.rastertools_window_size = shaded_snow.get("rastertools_window_size", 1024)
            self.rastertools_radius = shaded_snow.get("rastertools_radius", None)
        else:
            logging.warning("shaded_snow parameters are not defined, let-it-snow will not detect shaded snow.")
        
        
        # ----------------------------------------------------------------------
        # FSC
        # ----------------------------------------------------------------------
        fsc = data.get("fsc", None)
        if fsc is not None:
            logging.info("Load fsc parameters")

            self.tcd_file = fsc.get("tcd", None)
            self.fscOg_Eq = fsc.get("fscOg_Eq", "fscToc/(1-tcd)")
            self.fscToc_Eq = fsc.get("fscToc_Eq", "1.45*ndsi-0.01")

        else:
            logging.warning("fsc parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Water Mask
        # ----------------------------------------------------------------------
        water_mask = data.get("water_mask", None)
        if water_mask is not None:
            logging.info("Load water mask parameters")

            self.water_mask_path = water_mask.get('water_mask_path', None)
            self.water_mask_raster_values = water_mask.get('water_mask_raster_values', [1])

        else:
            logging.warning("water mask parameters are not defined, let-it-snow will used default values.")

        # ----------------------------------------------------------------------
        # Input
        # ----------------------------------------------------------------------
        input = data.get("inputs", None)
        if input is not None:
            logging.info("Load input parameters")

            div_mask = input.get("div_mask", None)
            if div_mask is not None:
                self.div_mask = div_mask  # surcharge avec la valeur dans le fichier de configuration

            div_slope_threshold = input.get("div_slope_thres", None)
            if div_slope_threshold is not None:
                self.div_slope_threshold = div_slope_threshold  # surcharge avec la valeur dans le fichier de configuration

            dem = input.get("dem", None)
            if dem is not None:
                self.dem = dem  # surcharge avec la valeur dans le fichier de configuration

            cloud_mask = input.get("cloud_mask", None)
            if cloud_mask is not None:
                self.cloud_mask = cloud_mask  # surcharge avec la valeur dans le fichier de configuration

            blue_band = input.get("blue_band", None)
            if blue_band is not None:
                blue_band_no_band = blue_band.get("no_band", None)
                if blue_band_no_band is not None:
                    self.blue_band_no_band = blue_band_no_band  # surcharge avec la valeur dans le fichier de configuration
                else:
                    if self.blue_band_no_band is None:
                        self.blue_band_no_band = 1  # default value
                blue_band_path = blue_band.get("path", None)
                if blue_band_path is not None:
                    self.blue_band_path = blue_band_path  # surcharge avec la valeur dans le fichier de configuration
            
            if self.blue_band_no_band is None:
                self.blue_band_no_band = 1  # default value

            green_band = input.get("green_band", None)
            if green_band is not None:
                green_band_no_band = green_band.get("no_band", None)
                if green_band_no_band is not None:
                    self.green_band_no_band = green_band_no_band  # surcharge avec la valeur dans le fichier de configuration
                else:
                    if self.green_band_no_band is None:
                        self.green_band_no_band = 1  # default value
                green_band_path = green_band.get("path", None)
                if green_band_path is not None:
                    self.green_band_path = green_band_path  # surcharge avec la valeur dans le fichier de configuration

            if self.green_band_no_band is None:
                self.green_band_no_band = 1  # default value

            red_band = input.get("red_band", None)
            if red_band is not None:
                red_band_no_band = red_band.get("no_band", None)
                if red_band_no_band is not None:
                    self.red_band_no_band = red_band_no_band  # surcharge avec la valeur dans le fichier de configuration
                else:
                    if self.red_band_no_band is None:
                        self.red_band_no_band = 1  # default value
                red_band_path = red_band.get("path", None)
                if red_band_path is not None:
                    self.red_band_path = red_band_path  # surcharge avec la valeur dans le fichier de configuration

            if self.red_band_no_band is None:
                self.red_band_no_band = 1  # default value

            swir_band = input.get("swir_band", None)
            if swir_band is not None:
                swir_band_no_band = swir_band.get("no_band", None)
                if swir_band_no_band is not None:
                    self.swir_band_no_band = swir_band_no_band  # surcharge avec la valeur dans le fichier de configuration
                else:
                    if self.swir_band_no_band is None:
                        self.swir_band_no_band = 1  # default value
                swir_band_path = swir_band.get("path", None)
                if swir_band_path is not None:
                    self.swir_band_path = swir_band_path  # surcharge avec la valeur dans le fichier de configuration

            if self.swir_band_no_band is None:
                self.swir_band_no_band = 1  # default value

            metadata = input.get("metadata", None)
            if metadata is not None:
                self.metadata = metadata  # surcharge avec la valeur dans le fichier de configuration

    def update_dem(self, dem):
        if dem is not None:
            self.dem = dem

        if self.dem is not None:
            if not os.path.exists(self.dem):
                msg = "Dem " + self.dem + " does not exist."
                logging.error(msg)
                raise LisConfigurationException(msg)
        else:
            msg = "Dem is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

    def update_relief_shadow_mask(self, relief_shadow_mask):
        if relief_shadow_mask is not None:
            self.relief_shadow_mask = relief_shadow_mask

        if self.relief_shadow_mask is not None:
            if not os.path.exists(self.relief_shadow_mask):
                msg = "relief_shadow_mask " + self.relief_shadow_mask + " does not exist."
                logging.error(msg)
                raise LisConfigurationException(msg)
        
        if self.detect_shaded_snow and (self.relief_shadow_mask is None) and (self.metadata is None):
            # If detect_shaded_snow is True, you need either the relief_shadow_mask or the metadata file
            msg= "No metadata nor relief_shadow_mask is given. One or the other should be defined in the configuration file"
            logging.error(msg)
            raise LisConfigurationException(msg)

    def update_tcd(self, tcd):
        logging.debug("tcd : %s", tcd)
        logging.debug("self.tcd_file : %s", self.tcd_file)
        if tcd is not None:
            self.tcd_file = tcd

        if self.tcd_file is not None and self.tcd_file:
            if not os.path.exists(self.tcd_file):
                msg = "Tree cover density " + self.tcd_file + " does not exist."
                logging.error(msg)
                raise LisConfigurationException(msg)
        else:
            msg = "Tree cover density is not defined."
            logging.warning(msg)
        # raise LisConfigurationException(msg)

    def update_water_mask(self, water_mask):
        if water_mask is not None:
            self.water_mask_path = water_mask

        if self.water_mask_path is not None and self.water_mask_path:
            if not os.path.exists(self.water_mask_path):
                msg = "Water mask " + self.water_mask_path + " does not exist."
                logging.error(msg)
                raise IOError(msg)
        else:
            msg = "Water mask density is not defined."
            logging.warning(msg)

    def read_product(self, input_dir):
        if input_dir is not None:
            if not os.path.exists(input_dir):
                msg = "Input dir" + input_dir + " does not exist."
                logging.error(msg)
                raise IOError(msg)

            basename = os.path.basename(input_dir)
            if not basename:
                basename = os.path.basename(os.path.dirname(input_dir))
            self.product_id = basename

            # unzip input if zipped
            if input_dir.lower().endswith('.zip'):
                zip_input = zipfile.ZipFile(input_dir)
                zip_input.extractall(path=basename)
                input_dir = basename

            # retrieve product mission/platform
            mission_key = self.retrieve_mission(input_dir)
            mission_config = mission_parameters.get(mission_key)

            if self.mission is MISSION_S2:
                id_split = self.product_id.split("_")
                self.tile_id = id_split[3]
                self.acquisition_date = id_split[1].split('-')[0] + "T" + id_split[1].split('-')[1]
            if self.mission is MISSION_L8:
                id_split = self.product_id.split("_")
                self.tile_id = id_split[5]
                self.acquisition_date = id_split[3]

            self.mode = mission_config.get("mode", None)
            self.multi = mission_config.get("multi", None)
            self.div_slope_threshold = mission_config.get("div_slope_threshold", None)

            m_blue_band = mission_config.get("blue_band", None)
            if m_blue_band is not None:
                self.blue_band_path = find_file(input_dir, m_blue_band)
            
            m_green_band = mission_config.get("green_band", None)
            if m_green_band is not None :
                self.green_band_path = find_file(input_dir, m_green_band)

            m_red_band = mission_config.get("red_band", None)
            if m_red_band is not None:
                self.red_band_path = find_file(input_dir, m_red_band)
            
            m_nir_band = mission_config.get("nir_band", None)
            if m_nir_band is not None:
                self.nir_band_path = find_file(input_dir, m_nir_band)

            m_swir_band = mission_config.get("swir_band", None)
            if m_swir_band is not None:
                self.swir_band_path = find_file(input_dir, m_swir_band)

            self.blue_band_no_band = mission_config.get("blue_band_number", None)
            self.green_band_no_band = mission_config.get("green_band_number", None)
            self.red_band_no_band = mission_config.get("red_band_number",  None)
            self.nir_band_no_band = mission_config.get("nir_band_number", None)
            self.swir_band_no_band = mission_config.get("swir_band_number", None)

            m_cloud_mask = mission_config.get("cloud_mask", None)
            if m_cloud_mask is not None:
                self.cloud_mask = find_file(input_dir, m_cloud_mask)

            m_div_mask = mission_config.get("div_mask", None)
            if m_div_mask is not None:
                logging.debug("m_div_mask : %s", m_div_mask)
                div_mask = find_file(input_dir, m_div_mask)
                if div_mask is not None:
                    self.div_mask = div_mask
            logging.debug("self.div_mask :%s", self.div_mask)

            m_dem = mission_config.get("dem", None)
            if m_dem is not None:
                logging.debug("m_dem : %s", m_dem)
                dem_found = find_file(input_dir, m_dem)
                if dem_found is not None:
                    self.dem = dem_found

            m_metadata = mission_config.get("metadata", None)
            if m_metadata is not None:
                logging.debug("m_metadata : {m_metadata}")
                metadata_found = find_file(input_dir, m_metadata)
                if metadata_found is not None:
                    self.metadata = metadata_found

            self.shadow_in_mask = mission_config.get("shadow_in_mask", None)
            self.shadow_out_mask = mission_config.get("shadow_out_mask", None)
            self.all_cloud_mask = mission_config.get("all_cloud_mask", None)
            self.high_cloud_mask = mission_config.get("high_cloud_mask", None)
            self.resize_factor = mission_config.get("resize_factor", None)

        # Check parameters
        self.check_input_parameters()

    def check_input_parameters(self):
        if self.red_band_path is not None:
            if not os.path.exists(self.red_band_path):
                msg = "Red band " + self.red_band_path + " does not exist."
                logging.error(msg)
                raise IOError()
        else:
            msg = "Red band is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)
        if self.green_band_path is not None:
            if not os.path.exists(self.green_band_path):
                msg = "Green band " + self.green_band_path + " does not exist."
                logging.error(msg)
                raise IOError(msg)
        else:
            msg = "Green band is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)
        if self.swir_band_path is not None:
            if not os.path.exists(self.swir_band_path):
                msg = "Swir band " + self.swir_band_path + " does not exist."
                logging.error(msg)
                raise IOError(msg)
        else:
            msg = "Swir band is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

        if self.detect_shaded_snow:
            if self.blue_band_path is not None:
                if not os.path.exists(self.blue_band_path):
                    msg = "Blue band " + self.blue_band_path + " does not exist."
                    logging.error(msg)
                    raise IOError()
            else:
                msg = "Blue band is not defined."
                logging.error(msg)
                raise LisConfigurationException(msg)
            
            if self.nir_band_path is not None:
                if not os.path.exists(self.nir_band_path):
                    msg = "NIR band " + self.nir_band_path + " does not exist."
                    logging.error(msg)
                    raise IOError()
            else:
                msg = "NIR band is not defined."
                logging.error(msg)
                raise LisConfigurationException(msg)
        
        if self.cloud_mask is not None:
            if not os.path.exists(self.cloud_mask):
                msg = "Cloud mask " + self.cloud_mask + " does not exist."
                logging.error(msg)
                raise IOError(msg)
        else:
            msg = "Cloud mask is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

        if self.div_mask is not None:
            if not os.path.exists(self.div_mask):
                logging.warning("div_mask was not found, the slope correction flag will be ignored")
        else:
            logging.warning("div_mask is not defined, the slope correction flag will be ignored")

        if self.div_slope_threshold is None:
            logging.warning("div_slope_threshold is not defined, the slope correction flag will be ignored")

        if self.metadata is not None:
            if not os.path.exists(self.metadata):
                msg = "Metadata " + str(self.metadata) + " with sun angles file is not defined."
                logging.error(msg)
                raise IOError(msg)

    
    def log_configuration(self):
        logging.debug("==== Configuration ====")

        logging.debug("== General ==")
        logging.debug("multi : " + str(self.multi))
        logging.debug("mode : " + str(self.mode))
        logging.debug("nb_threads : " + str(self.nb_threads))
        logging.debug("no_data : " + str(self.no_data))
        logging.debug("preprocessing : " + str(self.do_preprocessing))
        logging.debug("ram : " + str(self.ram))

        logging.debug("== Input ==")
        logging.debug("div_mask : " + str(self.div_mask))
        logging.debug("div_slope_threshold : " + str(self.div_slope_threshold))
        logging.debug("dem : " + str(self.dem))
        logging.debug("cloud_mask : " + str(self.cloud_mask))
        logging.debug("blue_band_noBand : " + str(self.blue_band_no_band))
        logging.debug("blue_band_path : " + str(self.blue_band_path))
        logging.debug("green_band_noBand : " + str(self.green_band_no_band))
        logging.debug("green_band_path : " + str(self.green_band_path))
        logging.debug("red_band_no_band : " + str(self.red_band_no_band))
        logging.debug("red_band_path : " + str(self.red_band_path))
        logging.debug("nir_band_no_band : " + str(self.nir_band_no_band))
        logging.debug("nir_band_path : " + str(self.nir_band_path))
        logging.debug("swir_band_no_band : " + str(self.swir_band_no_band))
        logging.debug("swir_band_path : " + str(self.swir_band_path))
        logging.debug("metadata : " + str(self.metadata))

        logging.debug("== Snow ==")
        logging.debug("dz : " + str(self.dz))
        logging.debug("ndsi_pass1 : " + str(self.ndsi_pass1))
        logging.debug("red_pass1 : " + str(self.red_pass1))
        logging.debug("ndsi_pass2 : " + str(self.ndsi_pass2))
        logging.debug("red_pass2 : " + str(self.red_pass2))
        logging.debug("fsnow_lim : " + str(self.fsnow_lim))
        logging.debug("fsnow_total_lim : " + str(self.fsnow_total_lim))
        logging.debug("fclear_lim : " + str(self.fclear_lim))
        
        logging.debug("== Shaded_snow ==")
        logging.debug("detect_shaded_snow : " + str(self.detect_shaded_snow))
        logging.debug("shaded_snow_pass : " + str(self.shaded_snow_pass))
        logging.debug("relief_shadow_mask : " + str(self.relief_shadow_mask))
        logging.debug("hillshade_lim : " + str(self.hillshade_lim))

        logging.debug("== Cloud ==")
        logging.debug("all_cloud_mask : " + str(self.all_cloud_mask))
        logging.debug("high_cloud_mask : " + str(self.high_cloud_mask))
        logging.debug("shadow_in_mask : " + str(self.shadow_in_mask))
        logging.debug("shadow_out_mask : " + str(self.shadow_out_mask))
        logging.debug("red_back_to_cloud : " + str(self.red_back_to_cloud))
        logging.debug("resize_factor : " + str(self.resize_factor))
        logging.debug("red_dark_cloud : " + str(self.red_dark_cloud))
        logging.debug("strict_cloud_mask : " + str(self.strict_cloud_mask))
        logging.debug("rm_snow_inside_cloud : " + str(self.rm_snow_inside_cloud))
        logging.debug("dilation_radius : " + str(self.dilation_radius))
        logging.debug("cloud_threshold : " + str(self.cloud_threshold))
        logging.debug("cloud_min_area_size : " + str(self.cloud_min_area_size))

        logging.debug("== Vector ==")
        logging.debug("generate_vector : " + str(self.generate_vector))
        logging.debug("generate_intermediate_vectors : " + str(self.generate_intermediate_vectors))
        logging.debug("use_gdal_trace_outline : " + str(self.use_gdal_trace_outline))
        logging.debug("gdal_trace_outline_dp_toler : " + str(self.gdal_trace_outline_dp_toler))
        logging.debug("gdal_trace_outline_min_area : " + str(self.gdal_trace_outline_min_area))

        logging.debug("== Water Mask ==")
        logging.debug("water_mask_path : " + str(self.water_mask_path))
        logging.debug("water_mask_raster_values : " + str(self.water_mask_raster_values))

        logging.debug("== FSC ==")
        logging.debug("tcd_file : " + str(self.tcd_file))
        logging.debug("fscOg_Eq : " + str(self.fscOg_Eq))
        logging.debug("fscToc_Eq : " + str(self.fscToc_Eq))

    def dump_configuration(self, dump_path, config_file, input_dir, log, chain_version, product_counter):
        # Get the fields as a dictionary
        conf_keys = ["dem", "tcd", "water_mask"]
        key_translation = {"tcd": "tcd_file", "water_mask": "water_mask_path"}
        full_data = vars(self)
        data = {key: full_data[key_translation.get(key, key)] for key in conf_keys}
        data["output_dir"] = dump_path
        data["input_dir"] = input_dir
        data["log"] = log
        data["config_file"] = config_file
        data["chain_version"] = chain_version
        data["product_counter"] = product_counter
        file_path = os.path.join(dump_path, 'fsc_config.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def retrieve_mission(self, absoluteFilename):
        mission_key = None
        if '.SAFE' in absoluteFilename:
            # L2A SEN2COR product
            logging.info("SEN2COR product detected (detect .SAFE in the input path...).")
            mission_key = "SEN2COR"
            self.mission = MISSION_S2
        elif '.DBL.DIR' in absoluteFilename:
            if any(s in absoluteFilename for s in sentinel2Acronyms):
                logging.info("MAJA native product detected (detect .DBL.DIR substring in input path...)")
                mission_key = "MAJA"
                self.mission = MISSION_S2
            else:
                msg = "Only MAJA products from Sentinels are supported."
                logging.error(msg)
                raise IOError(msg)
        elif any(s in absoluteFilename for s in sentinel2Acronyms):
            logging.info("THEIA Sentinel product detected.")
            mission_key = "S2"
            self.mission = MISSION_S2
        elif "Take5" in absoluteFilename:
            logging.info("THEIA Take5 product detected.")
            mission_key = "Take5"
            self.mission = MISSION_T5
        elif "LANDSAT8-OLITIRS-XS" in absoluteFilename:
            logging.info("THEIA LANDSAT8 product detected. (new version)")
            mission_key = "LANDSAT8_new_format"
            self.mission = MISSION_L8
        elif "LANDSAT8" in absoluteFilename:
            logging.info("THEIA LANDSAT8 product detected.")
            mission_key = "LANDSAT8"
            self.mission = MISSION_L8
        elif "LC08" in absoluteFilename:
            logging.info("LANDSAT8 LASRC) product detected (LC08_L1TP in input path...).")
            mission_key = "LANDSAT8_LASRC"
            self.mission = MISSION_L8
        else:
            msg = "Unknown product type."
            logging.error(msg)
            raise UnknownProductException(msg)

        return mission_key
