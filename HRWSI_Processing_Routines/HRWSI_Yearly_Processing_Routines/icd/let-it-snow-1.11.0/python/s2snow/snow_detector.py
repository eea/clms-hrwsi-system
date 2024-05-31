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
import os
import os.path as op
import shutil
import numpy as np
import scipy.ndimage as nd
from lxml import etree
from s2snow.hillshade import (compute_hillshade_mask,
                              compute_hillshade_mask_rastertools)
from otbApplication import ImagePixelType_uint8
from s2snow.cloud_extraction import (extract_all_clouds,
                                     extract_back_to_cloud_mask,
                                     extract_cloud_shadows,
                                     extract_high_clouds, refine_cloud_mask)
from s2snow.dem_builder import build_dem
from s2snow.gdal_wrappers import (extract_band, extract_red_band,
                                  extract_red_nn, initialize_vrt,
                                  update_cloud_mask, update_snow_mask)
from s2snow.lis_constant import (BLUE, CLOUD_PASS1, DEM_RESAMPLED, DOI_URL,
                                 FSCTOC, FSCTOCHS, GDAL_OPT, GREEN,
                                 HILLSHADE_MASK, HISTOGRAM, LABEL_CLOUD,
                                 LABEL_NO_DATA, LABEL_SNOW, METADATA,
                                 MISSION_S2, MODE_SENTINEL2, N_BLUE, N_GREEN,
                                 N_NIR, N_RED, N_SWIR, NDSI, NIR, NO_DATA_MASK,
                                 RED, SHADED_SNOW, SLOPE_MASK, SNOW_ALL,
                                 SNOW_MASK, SNOW_PASS1, SNOW_PASS2,
                                 SNOW_PASS2_VEC, SNOW_PASS3, SNOW_PASS3_VEC,
                                 SNOW_VEC, SWIR, TMP_DIR,
                                 UNCALIBRATED_SHADED_SNOW)
from s2snow.otb_wrappers import band_math, compute_snow_line, compute_snow_mask
from s2snow.qc_flags import edit_lis_fsc_qc_layers
from s2snow.resolution import (adapt_to_target_resolution,
                               define_band_resolution)
from s2snow.utils import (compute_percent, edit_nodata_value,
                          edit_raster_from_raster, edit_raster_from_shapefile,
                          get_raster_as_array, polygonize)

from importlib.metadata import version


def detect_snow(config, output_dir, chain_version=None, product_counter=None):
    logging.info("--------------------")
    logging.info("Start snow detection")
    logging.info("--------------------")

    # Set maximum ITK threads
    if config.nb_threads:
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(config.nb_threads)
    logging.debug("threads number : " + str(config.nb_threads))

    tmp_dir = os.path.join(output_dir, TMP_DIR)

    # manage slope mask
    logging.info("Manage slope.")
    slope_mask_file = manage_slope_mask(config.div_mask, config.div_slope_threshold, tmp_dir,
                                        ram=config.ram)

    # manage target resolution
    logging.info("Manage target resolution.")
    logging.debug("Extract bands")
    green_extracted_band = extract_band(GREEN, config.green_band_path, config.green_band_no_band,
                                        tmp_dir, no_data=config.no_data)
    red_extracted_band = extract_band(RED, config.red_band_path, config.red_band_no_band,
                                      tmp_dir, no_data=config.no_data)
    swir_extracted_band = extract_band(SWIR, config.swir_band_path, config.swir_band_no_band,
                                       tmp_dir, no_data=config.no_data)
    if config.detect_shaded_snow:
        logging.debug("Extract bands Blue and NIR")
        blue_extracted_band = extract_band(BLUE, config.blue_band_path, config.blue_band_no_band, tmp_dir,
                                           no_data=config.no_data)
        nir_extracted_band = extract_band(NIR, config.nir_band_path, config.nir_band_no_band, tmp_dir,
                                          no_data=config.no_data)
    else:
        logging.debug("Ignoring bands Blue and NIR")
        blue_extracted_band = None
        nir_extracted_band = None

    logging.info("Define bands resolution.")
    gb_resolution = define_band_resolution(green_extracted_band)
    logging.debug(GREEN + " band resolution : " + str(gb_resolution))
    rb_resolution = define_band_resolution(red_extracted_band)
    logging.debug(RED + " band resolution : " + str(rb_resolution))
    sb_resolution = define_band_resolution(swir_extracted_band)
    logging.debug(SWIR + " band resolution : " + str(sb_resolution))

    if config.detect_shaded_snow:
        bb_resolution = define_band_resolution(blue_extracted_band)
        logging.debug(BLUE + " band resolution : " + str(bb_resolution))
        nb_resolution = define_band_resolution(nir_extracted_band)
        logging.debug(NIR + " band resolution : " + str(nb_resolution))
    else:
        bb_resolution = rb_resolution
        nb_resolution = rb_resolution

    logging.info("Define target resolution.")
    tg_resolution = max(bb_resolution, gb_resolution, rb_resolution, nb_resolution, sb_resolution)
    logging.debug("Target resolution :" + str(tg_resolution))

    logging.info("Adapt bands resolution to target resolution.")
    green_band_resampled = adapt_to_target_resolution(GREEN, gb_resolution, tg_resolution, green_extracted_band,
                                                      tmp_dir)
    red_band_resampled = adapt_to_target_resolution(RED, rb_resolution, tg_resolution, red_extracted_band,
                                                    tmp_dir)
    swir_band_resampled = adapt_to_target_resolution(SWIR, sb_resolution, tg_resolution, swir_extracted_band,
                                                     tmp_dir)

    if config.detect_shaded_snow:
        blue_band_resampled = adapt_to_target_resolution(BLUE, bb_resolution, tg_resolution, blue_extracted_band,
                                                         tmp_dir)
        nir_band_resampled = adapt_to_target_resolution(NIR, nb_resolution, tg_resolution, nir_extracted_band, tmp_dir)
    else:
        blue_band_resampled = None
        nir_band_resampled = None

    # manage water mask
    logging.info("Manage water mask")
    manage_water_mask(green_band_resampled, red_band_resampled, swir_band_resampled, config.water_mask_path,
                      config.water_mask_raster_values, no_data=config.no_data, blue_band_resampled=blue_band_resampled,
                      nir_band_resampled=nir_band_resampled)

    # build vrt
    logging.info("Initialize image vrt")
    img_vrt = initialize_vrt(swir_band_resampled, red_band_resampled, green_band_resampled, tmp_dir,
                             blue_band_resampled, nir_band_resampled)

    # External preprocessing
    logging.info("Manage dem")
    dem = manage_dem(img_vrt, config.dem, tmp_dir, config.do_preprocessing, nb_thread=config.nb_threads,
                     ram=config.ram)

    logging.info("Reading Relief shadow mask")
    if config.detect_shaded_snow and (config.relief_shadow_mask is None):
        logging.info("No relief shadow mask provided, computing it")
        relief_shadow_mask = op.join(tmp_dir, HILLSHADE_MASK)
        if not config.rastertools_use:
            logging.info("Use classic hillshade methods as requested in configuration file.")
            compute_hillshade_mask(relief_shadow_mask, dem, config.hillshade_lim, config.metadata, tmp_dir)
        else:
            try:
                logging.info("Use rastertools hillshade methods.")
                compute_hillshade_mask_rastertools(relief_shadow_mask, dem, config.metadata, tmp_dir, tg_resolution,
                                                    config.rastertools_window_size, config.rastertools_radius)
            except Exception as err:
                logging.error(f"Rastertools hillshade methods encountered an error : {err}")
                raise
    else:
        relief_shadow_mask = config.relief_shadow_mask

    # Initialize the no_data mask
    logging.info("Initialize no_data mask")
    no_data_mask_file = initialize_no_data_mask(img_vrt, tmp_dir, no_data=config.no_data, ram=config.ram)

    logging.info("Launch pass0")
    # Extract red band
    red_band_file = extract_red_band(img_vrt, tmp_dir, no_data=config.no_data)
    logging.info("Extract red nn")
    red_nn_file = extract_red_nn(red_band_file, tmp_dir, resize_factor=config.resize_factor)

    # Extract all cloud masks
    logging.info("Extract all clouds")
    all_cloud_mask_file = extract_all_clouds(config.cloud_mask, tmp_dir, config.all_cloud_mask,
                                             config.mode, config.ram)

    # Extract cloud shadows mask
    logging.info("Extract cloud shadows")
    shadow_mask_file = extract_cloud_shadows(config.cloud_mask, tmp_dir, config.mode,
                                             config.shadow_in_mask,
                                             config.shadow_out_mask, config.ram)

    # Extract high clouds
    logging.info("Extract high clouds")
    high_cloud_mask_file = extract_high_clouds(config.cloud_mask, tmp_dir, config.high_cloud_mask,
                                               config.mode,
                                               config.ram)

    # Extract also a mask for condition back to cloud
    logging.info("Extract back to cloud mask")
    mask_back_to_cloud_file = extract_back_to_cloud_mask(config.cloud_mask, red_band_file, tmp_dir,
                                                         config.red_back_to_cloud, config.mode, config.ram)

    ndsi_formula = "(im1b" + str(N_GREEN) + "-im1b" + str(N_SWIR) + ")/(im1b" + str(N_GREEN) + "+im1b" + str(
        N_SWIR) + ")"
    logging.info("ndsi formula : " + ndsi_formula)

    logging.info("Launch pass1")
    logging.info("Compute snow pass 1")
    snow_pass1_file = compute_snow_pass1(img_vrt, all_cloud_mask_file, tmp_dir, ndsi_formula, config.ndsi_pass1,
                                         config.red_pass1, ram=config.ram)

    # create a working copy of all cloud mask
    cloud_pass1_file = op.join(tmp_dir, CLOUD_PASS1)
    logging.info("Create working copy of all cloud mask file : " + cloud_pass1_file)
    shutil.copy(all_cloud_mask_file, cloud_pass1_file)

    # apply pass 1.5 to discard uncertain snow area
    # warn this function update in-place both snow and cloud mask
    if config.rm_snow_inside_cloud:
        logging.info("Remove snow inside cloud")
        remove_snow_inside_cloud(snow_pass1_file, cloud_pass1_file, config.dilation_radius, config.cloud_threshold,
                                 config.cloud_min_area_size)

    # The computation of cloud refine is done below,
    # because the inital cloud may be updated within pass1_5
    logging.info("Refine cloud")
    cloud_refine_file = refine_cloud_mask(all_cloud_mask_file, shadow_mask_file, red_nn_file, high_cloud_mask_file,
                                          cloud_pass1_file, tmp_dir,
                                          red_dark_cloud=config.red_dark_cloud,
                                          ram=config.ram)

    logging.info("Launch pass2")
    # Compute snow fraction in the pass1 image (including nodata pixels)
    snow_fraction = compute_percent(snow_pass1_file, 1) / 100
    logging.info("Snow fraction in pass1 image:" + str(snow_fraction))

    # Compute Zs elevation fraction and histogram values
    # We compute it in all case as we need to check histogram values to
    # detect cold clouds in optional pass4
    logging.info("Compute snow line")
    histogram_file = op.join(tmp_dir, HISTOGRAM)
    zs = compute_snow_line(dem,
                           snow_pass1_file,
                           cloud_pass1_file,
                           config.dz,
                           config.fsnow_lim,
                           config.fclear_lim,
                           False,
                           -2,
                           -config.dz / 2,
                           histogram_file,
                           config.ram)
    logging.info("computed ZS:" + str(zs))

    snow_pass2_file = None
    shaded_snow_file = None
    uncalibrated_shaded_snow_mask = None

    if snow_fraction > config.fsnow_total_lim:
        # Test zs value (-1000 means that no zs elevation was found)
        if zs != -1000:
            logging.info("Compute snow pass 2")
            snow_pass2_file = compute_snow_pass2(img_vrt, dem, cloud_refine_file, tmp_dir, ndsi_formula,
                                                 config.ndsi_pass2, config.red_pass2, zs, ram=config.ram)
            compute_snow_pass2_vec(snow_pass2_file,
                                   tmp_dir,
                                   config.generate_intermediate_vectors,
                                   config.use_gdal_trace_outline, config.gdal_trace_outline_min_area,
                                   config.gdal_trace_outline_dp_toler)
            if config.detect_shaded_snow:
                shaded_snow_file = compute_shaded_snow(img_vrt,
                                                       dem,
                                                       relief_shadow_mask,
                                                       cloud_refine_file,
                                                       tmp_dir,
                                                       config.shaded_snow_pass,
                                                       zs,
                                                       ram=config.ram)

                uncalibrated_shaded_snow_mask = compute_uncalibrated_shaded_snow_mask(snow_pass1_file,
                                                                                      snow_pass2_file,
                                                                                      tmp_dir,
                                                                                      shaded_snow_file,
                                                                                      ram=config.ram)
        else:
            logging.warning("Zs elevation was not found, artificially setting Zs to 1e9 to generate QC required data.")
            zs = 1e9
            logging.info("Compute snow pass 2")
            snow_pass2_file = compute_snow_pass2(img_vrt, dem, cloud_refine_file, tmp_dir, ndsi_formula,
                                                 config.ndsi_pass2, config.red_pass2, zs, ram=config.ram)
            compute_snow_pass2_vec(snow_pass2_file,
                                   tmp_dir,
                                   config.generate_intermediate_vectors,
                                   config.use_gdal_trace_outline, config.gdal_trace_outline_min_area,
                                   config.gdal_trace_outline_dp_toler)
            if config.detect_shaded_snow:
                shaded_snow_file = compute_shaded_snow(img_vrt,
                                                       dem,
                                                       relief_shadow_mask,
                                                       cloud_refine_file,
                                                       tmp_dir,
                                                       config.shaded_snow_pass,
                                                       zs,
                                                       ram=config.ram)

                uncalibrated_shaded_snow_mask = compute_uncalibrated_shaded_snow_mask(snow_pass1_file,
                                                                                      snow_pass2_file,
                                                                                      tmp_dir,
                                                                                      shaded_snow_file,
                                                                                      ram=config.ram)
    else:
        logging.warning("Snow fraction in snow pass 1 is under fsnow_total_lim.")

    # Compute pass3 = fusion between pass 2 and pass 1
    logging.info("Compute snow pass 3")
    generic_snow_path = compute_snow_pass3(snow_pass1_file, snow_pass2_file, tmp_dir, shaded_snow_file, ram=config.ram)

    if snow_pass2_file is None:
        snow_pass2_file = op.join(tmp_dir, SNOW_PASS2)
        band_math([snow_pass1_file], snow_pass2_file + GDAL_OPT, "0", config.ram, ImagePixelType_uint8)

    compute_snow_pass3_vec(generic_snow_path, tmp_dir, config.generate_intermediate_vectors,
                           config.use_gdal_trace_outline,
                           config.gdal_trace_outline_min_area, config.gdal_trace_outline_dp_toler)

    # Final update of the snow  mask (include snow/nosnow/cloud)
    logging.info("Compute final mask")
    final_mask_file = compute_final_mask(cloud_refine_file, generic_snow_path, mask_back_to_cloud_file,
                                         no_data_mask_file, tmp_dir, config.strict_cloud_mask, mode=config.mode,
                                         ram=config.ram)

    # Compute the complete snow mask
    snow_all_file = op.join(tmp_dir, SNOW_ALL)
    logging.info("Compute snow all file")
    compute_snow_mask(snow_pass1_file, snow_pass2_file, cloud_pass1_file, cloud_refine_file,
                      all_cloud_mask_file, snow_all_file, slope_mask_file, config.ram,
                      ImagePixelType_uint8)

    # FSC has not been validated yet for L8 and Take5
    if config.mission is MISSION_S2:
        logging.info("Compute NDSI")
        ndsi_file = compute_ndsi(img_vrt, final_mask_file, tmp_dir, ndsi_formula, ram=config.ram)

        logging.info("Compute FSC TOC")
        fsc_toc_file = compute_fsc_toc(ndsi_file, final_mask_file, tmp_dir, config.fscToc_Eq, ram=config.ram)

        if uncalibrated_shaded_snow_mask is not None:
            logging.info("Adjust FSC TOC for hill shade")
            fsc_toc_file = adjust_for_hillshade(uncalibrated_shaded_snow_mask, fsc_toc_file, tmp_dir, ram=config.ram)

        logging.info("Compute final fsc product name")
        if config.tcd_file is not None:
            name = compute_final_fsc_name(config.mission, config.tile_id, config.acquisition_date,
                                          chain_version=chain_version, product_counter=product_counter)
            logging.info("fsc product name : %s", name)
            logging.info("Compute FSC OG")
            fsc_og_file = compute_fsc_og(name, fsc_toc_file, config.tcd_file, final_mask_file, output_dir,
                                         config.fscOg_Eq, ram=config.ram)

            logging.info("Compute QC Flags")
            qc_flags_file = edit_lis_fsc_qc_layers(fsc_toc_file, config.cloud_mask, config.div_mask,  tmp_dir,
                                                   fsc_og_file=fsc_og_file, water_mask_path=config.water_mask_path,
                                                   tcd_path=config.tcd_file, shaded_snow_path=shaded_snow_file)
            if qc_flags_file is not None:
                qc_name = compute_final_fsc_name(config.mission, config.tile_id, config.acquisition_date,
                                                 chain_version=chain_version, product_counter=product_counter,
                                                 is_qcflags=True)
                logging.info("qcflags product name : %s", name)
                shutil.copy(qc_flags_file, op.join(output_dir, qc_name))

        else:
            logging.warning("Tree cover density file is not defined, FSC on ground can not be computed.")
            name = compute_final_fsc_name(config.mission, config.tile_id, config.acquisition_date,
                                          chain_version=chain_version, product_counter=product_counter, is_toc=True)
            logging.info("fsc product name : %s", name)
            shutil.copy(fsc_toc_file, op.join(output_dir, name))

            logging.info("Compute TOC QC Flags")
            edit_lis_fsc_qc_layers(fsc_toc_file, config.cloud_mask, config.div_mask, tmp_dir, shaded_snow_path=shaded_snow_file)
    else:
        name = compute_final_fsc_name(config.mission, config.tile_id, config.acquisition_date,
                                      chain_version=chain_version, product_counter=product_counter, is_mask=True)
        logging.info("snow product name : %s", name)
        shutil.copy(final_mask_file, op.join(output_dir, name))

    logging.info("Compute final snow vector")
    compute_final_snow_vec(final_mask_file, tmp_dir, config.generate_vector, config.use_gdal_trace_outline,
                           config.gdal_trace_outline_min_area, config.gdal_trace_outline_dp_toler)

    logging.info("Compute metadata")
    create_metadata(final_mask_file, output_dir, config.product_id, zs)

    logging.info("-------------------")
    logging.info("End snow detection")
    logging.info("-------------------")


def compute_final_fsc_name(mission, tile_id, acquisition_date, chain_version=None, product_counter=None, is_toc=None,
                           is_qcflags=None, is_mask=False):
    """
    Compute final fsc product name
    :param chain_version: h2 chain version
    :param mission: mission (S2 or L8 or T5)
    :param tile_id: tile_id
    :param acquisition_date: acquisition date
    :param product_counter: number of product
    :param is_toc: is final fsc is TOC level
    :param is_qcflags : is qc flags file
    :return: name defined
    """
    name = "LIS_" + mission + "-SNOW"

    if is_mask:
        name = name + "-MSK"
    else:
        name = name + "-FSC"
        if is_toc:
            name = name + "-TOC"
        else:
            if is_qcflags:
                name = name + "-QCFLAGS"

    if tile_id is not None:
        name = name + "_"+ tile_id

    if acquisition_date is not None:
        name = name + "_" + acquisition_date

    if chain_version is not None:
        name = name + "_" + chain_version
    else:
        name = name + "_" + version('s2snow')

    if product_counter is not None:
        name = name + "_" + product_counter

    name = name + ".tif"
    return name


def manage_dem(img_vrt, input_dem, tmp_dir, do_preprocessing, nb_thread=1, ram=512):
    """
    Manage dem
    :param img_vrt: lis vrt
    :param input_dem: input dem
    :param tmp_dir: temp directory
    :param do_preprocessing: flag if prepocessing is needed. (preprocessing = True in lis configuration file)
    :param nb_thread: nb_thred for otb call
    :param ram: ram for otb call
    :return: dem
    """
    if do_preprocessing:
        logging.debug("Launch dem preprocessing.")
        logging.debug("img_vrt : " + img_vrt)
        logging.debug("input_dem : " + input_dem)
        dem_resampled_file = op.join(tmp_dir, DEM_RESAMPLED)
        logging.debug("dem_resampled : " + dem_resampled_file)
        build_dem(input_dem, img_vrt, dem_resampled_file, ram, nb_thread)
        dem = dem_resampled_file
    else:
        logging.info("No dem preprocessing.")
        dem = input_dem
    logging.info("dem : " + dem)
    return dem


def initialize_no_data_mask(img_vrt, tmp_dir, no_data=-10000, ram=512):
    """
    Initialize no data mask
    :param img_vrt: lis vrt
    :param tmp_dir: temp directory
    :param no_data: no_data value - default ie -10000
    :param ram: ram for otb call - default is 512
    :return: no data mask.
    """
    logging.debug("Initialize no data mask.")
    logging.debug("img_vrt : %s", img_vrt)
    logging.debug("no_data : %s", str(no_data))
    logging.debug("ram : %s", str(ram))

    no_data_mask_expr = "im1b1==" + str(no_data) + "?1:0"
    logging.debug("Initialize no data mask with expression : " + no_data_mask_expr)

    no_data_mask_file = op.join(tmp_dir, NO_DATA_MASK)
    logging.info("No data mask : %s", no_data_mask_file)

    band_math([img_vrt], no_data_mask_file, no_data_mask_expr, ram)

    return no_data_mask_file


def manage_water_mask(green_band_resampled, red_band_resampled, swir_band_resampled, water_mask_path,
                      water_mask_raster_values, no_data=-10000, blue_band_resampled=None, nir_band_resampled=None):
    """
    Manage water mask
    :param blue_band_resampled: blue band
    :param green_band_resampled: green band
    :param red_band_resampled: red band
    :param nir_band_resampled: nir band
    :param swir_band_resampled: swir band
    :param water_mask_path: water mask
    :param water_mask_raster_values: water mask values
    :param no_data: no data default is -10000
    :return: nothing, bands are updated
    """
    wm_path = water_mask_path
    if wm_path is not None:
        if os.path.exists(wm_path):
            logging.debug("Water mask applies.")
            logging.debug("green_band_resampled: " + green_band_resampled)
            logging.debug("red_band_resampled : " + red_band_resampled)
            logging.debug("swir_band_resampled : " + swir_band_resampled)

            if blue_band_resampled is not None:
                logging.debug("blue_band_resampled : " + blue_band_resampled)
            else:
                logging.debug("blue_band_resampled : None")
            if nir_band_resampled is not None:
                logging.debug("nir_band_resampled : " + nir_band_resampled)
            else:
                logging.debug("nir_band_resampled : None")
            logging.debug("water_mask_path : " + wm_path)

            wm_raster_values = water_mask_raster_values
            logging.debug("water_mask_raster_values : " + str(wm_raster_values))
            logging.debug("no_data: " + str(no_data))

            water_mask_type = wm_path.split('.')[-1].lower()
            logging.debug("Water mask type : " + water_mask_type)

            if water_mask_type == 'tif':
                edit_raster_from_raster(green_band_resampled, wm_path,
                                        src_values=wm_raster_values,
                                        applied_value=no_data)
                edit_raster_from_raster(red_band_resampled, wm_path,
                                        src_values=wm_raster_values,
                                        applied_value=no_data)
                edit_raster_from_raster(swir_band_resampled, wm_path,
                                        src_values=wm_raster_values,
                                        applied_value=no_data)

                if blue_band_resampled is not None:
                    edit_raster_from_raster(blue_band_resampled, wm_path,
                                            src_values=wm_raster_values,
                                            applied_value=no_data)
                if nir_band_resampled is not None:
                    edit_raster_from_raster(nir_band_resampled, wm_path,
                                            src_values=wm_raster_values,
                                            applied_value=no_data)

            elif water_mask_type == 'shp':
                edit_raster_from_shapefile(green_band_resampled, wm_path, applied_value=no_data)
                edit_raster_from_shapefile(red_band_resampled, wm_path, applied_value=no_data)
                edit_raster_from_shapefile(swir_band_resampled, wm_path, applied_value=no_data)

                if blue_band_resampled is not None:
                    edit_raster_from_shapefile(blue_band_resampled, wm_path, applied_value=no_data)
                if nir_band_resampled is not None:
                    edit_raster_from_shapefile(nir_band_resampled, wm_path, applied_value=no_data)
            else:
                msg = 'Input water_mask_path must either be a GeoTIFF raster (.tif) or a shapefile (.shp)'
                logging.error(msg)
                raise IOError(msg)
        else:
            msg = "Input water_mask_path does not exist."
            logging.error(msg)
            raise IOError(msg)
    else:
        msg = 'Input water_mask_path does not exists. Water Mask will not be applied.'
        logging.warning(msg)


def manage_slope_mask(div_mask, div_slope_threshold, tmp_dir, ram=512):
    """
        Manage slope mask.
        :param div_mask: the div mask
        :param div_slope_threshold: the div_slope_threshold
        :param tmp_dir: the output directory
        :param ram: default is 512
        :return: slope_mask_file
    """
    if div_mask is not None:
        if div_slope_threshold is not None:
            logging.debug("Manage slope mask.")
            logging.debug("div_mask : " + div_mask)
            logging.debug("div_slope_thres : " + str(div_slope_threshold))

            slope_mask_file = op.join(tmp_dir, SLOPE_MASK)
            logging.info("slope_mask_file : " + slope_mask_file)

            # Extract the bad slope correction flag
            expr = "im1b1>=" + str(div_slope_threshold) + "?1:0"
            logging.debug("expression : " + expr)

            band_math([div_mask], slope_mask_file, expr, ram, out_type=ImagePixelType_uint8)

            return slope_mask_file
        else:
            logging.warning("div_slope_threshold is not defined, the slope correction flag will be ignored")
    else:
        logging.warning("div_mask is not defined, the slope correction flag will be ignored")


def compute_snow_pass1(img_vrt, all_cloud_mask_file, tmp_dir, ndsi_formula, ndsi_pass1, red_pass1, ram=512):
    """
    Compute snow pass 1
    :param img_vrt: lis vrt
    :param all_cloud_mask_file: all cloud mask file
    :param tmp_dir: temp directory
    :param ndsi_formula:  ndsi formula
    :param ndsi_pass1: ndsi condition for pass 1
    :param red_pass1: red confition for pass 1
    :param ram: ram for otb call default is 512
    :return: snow pass 1 file
    """
    # NDSI condition (ndsi > x and not cloud)
    condition_ndsi = "(im2b1!=1 and (" + ndsi_formula + ")>" + str(ndsi_pass1) + " "
    logging.debug("condition_ndsi : " + condition_ndsi)

    condition_pass1 = condition_ndsi + " and im1b" + str(N_RED) + "> " + str(red_pass1) + ")"
    logging.debug("condition_pass1 : " + condition_pass1)

    pass1_file = op.join(tmp_dir, SNOW_PASS1)
    logging.info("snow_pass1_file : " + pass1_file)

    band_math([img_vrt, all_cloud_mask_file], pass1_file + GDAL_OPT, condition_pass1 + "?1:0", ram)

    return pass1_file


def remove_snow_inside_cloud(snow_mask_file, cloud_mask_file, radius=1, cloud_threshold=0.85, min_area_size=25000):
    """
    Remove snow inside cloud
    :param snow_mask_file: snow mask file
    :param cloud_mask_file: cloud mask file
    :param radius: dilation_radius
    :param cloud_threshold: cloud threshold
    :param min_area_size: min area size
    :return: nothing, input snow mask and input cloud mask are updated
    """

    logging.debug("Retrieve snow and cloud mask as array.")
    snow_mask = get_raster_as_array(snow_mask_file)
    cloud_mask = get_raster_as_array(cloud_mask_file)

    snow_mask_init = np.copy(snow_mask)

    discarded_snow_area = 0

    (snow_labels, nb_label) = nd.measurements.label(snow_mask)
    logging.debug("There is " + str(nb_label) + " snow areas")

    # build the structuring element for dilation
    logging.debug("Build the structuring element for dilation.")
    struct = np.zeros((2 * radius + 1, 2 * radius + 1))
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    mask = x ** 2 + y ** 2 <= radius ** 2
    struct[mask] = 1

    # compute individual snow area size
    logging.debug("Compute individual snow area size.")
    (labels, label_counts) = np.unique(snow_labels, return_counts=True)
    labels_area = dict(list(zip(labels, label_counts)))
    logging.debug(labels_area)

    logging.debug("Start loop on snow areas")

    # For each snow area
    for lab in range(1, nb_label + 1):
        # Compute external contours
        logging.debug("Processing area " + str(lab))
        current_mask_area = labels_area[lab]
        logging.debug("Current area size = " + str(current_mask_area))
        if current_mask_area > min_area_size:
            logging.debug("Processing snow area of size = " + str(current_mask_area))
            current_mask = np.where(snow_labels == lab, 1, 0)
            patch_neige_dilat = nd.binary_dilation(current_mask, struct)
            logging.debug("Contour processing start")
            contour = np.where((snow_mask == 0) & (patch_neige_dilat == 1))

            # Compute percent of surrounding cloudy pixels
            cloud_contour = cloud_mask[contour]
            # print(cloud_contour)
            logging.debug("Contour processing done.")

            result = np.bincount(cloud_contour)
            logging.debug(result)
            cloud_percent = 0
            if len(result) > 1:
                cloud_percent = float(result[1]) / (result[0] + result[1])
                logging.debug(result)
                logging.debug(", " + str(cloud_percent * 100) + "% of surrounding cloud")

            # Discard snow area where cloud_percent > threshold
            if cloud_percent > cloud_threshold:
                logging.debug("Updating snow mask...")
                discarded_snow_area += 1
                snow_mask = np.where(snow_labels == lab, 0, snow_mask)
                logging.debug("Updating snow mask...Done")
                logging.debug("End of processing area " + str(lab))

    logging.debug(str(discarded_snow_area) + ' labels entoures de nuages (sur ' + str(nb_label) + ' labels)')

    (_, nb_label) = nd.measurements.label(snow_mask)

    logging.debug(str(nb_label) + ' labels snow after correction')

    # Update cloud mask with discared snow area
    logging.debug("Update cloud mask with discared snow area.")
    update_cloud_mask(snow_mask, cloud_mask, snow_mask_init, cloud_mask_file)

    # Update snow mask
    logging.debug("Update snow mask.")
    update_snow_mask(snow_mask, snow_mask_file)


def compute_snow_pass2(img_vrt, dem, cloud_refine_file, tmp_dir, ndsi_formula, ndsi_pass2, red_pass2, zs,
                       ram=512):
    """
    Compute snow pass 2.
    :param img_vrt: lis vrt
    :param dem: dem
    :param cloud_refine_file: cloud refine file
    :param tmp_dir: temp directory
    :param ndsi_formula:  ndsi formula
    :param ndsi_pass2:  ndsi condition for pass 2
    :param red_pass2: red condition for pass 2
    :param zs: zs
    :param ram: ram for otb call default is 512
    :return: snow pass 2 file
    """
    condition_pass2 = "(im3b1 != 1) and (im2b1>" + str(zs) + ")" \
                      + " and (" + ndsi_formula + "> " + str(ndsi_pass2) + ")" \
                      + " and (im1b" + str(N_RED) + ">" + str(red_pass2) + ")"

    logging.debug("condition_pass2 : " + condition_pass2)

    snow_pass2_file = op.join(tmp_dir, SNOW_PASS2)

    band_math([img_vrt, dem, cloud_refine_file], snow_pass2_file + GDAL_OPT,
              condition_pass2 + "?1:0", ram)
    return snow_pass2_file


def compute_snow_pass2_vec(snow_pass2_file, tmp_dir, generate_intermediate_vectors, use_gdal_trace_outline,
                           gdal_trace_outline_min_area, gdal_trace_outline_dp_toler):
    """
    Compute snow pass 2 vector.
    :param snow_pass2_file: snow pass 2 file
    :param tmp_dir: tem directory
    :param generate_intermediate_vectors: flag if vector should be generated
    :param use_gdal_trace_outline: Generate vector mask using gdal_trace_outline from gina_tools.
    :param gdal_trace_outline_min_area: Minimum area to keep in vector mask when using gdal_trace_outline
    :param gdal_trace_outline_dp_toler: Tolered pixel approximation in vector mask when using gdal_trace_outline
    (0 no approximation).
    :return: snow pass 2 file as vector.
    """
    snow_pass2_vec_file = op.join(tmp_dir, SNOW_PASS2_VEC)
    if generate_intermediate_vectors:
        # Generate polygons for pass2 (useful for quality check)
        polygonize(snow_pass2_file, snow_pass2_file, snow_pass2_vec_file, use_gdal_trace_outline,
                   gdal_trace_outline_min_area, gdal_trace_outline_dp_toler)
    return snow_pass2_vec_file


def compute_shaded_snow(img_vrt, dem, relief_shadow_mask, cloud_refine_file, tmp_dir, shaded_snow_pass, zs,
                        ram=512):
    """
    Compute shaded snow.
    :param img_vrt: lis vrt
    :param relief_shadow_mask: relief shadow mask
    :param cloud_refine_file: cloud refine file
    :param tmp_dir: temp directory
    :param shaded_snow_pass: threshold over which pixel is detected as snow
    :param zs: zs
    :param ram: ram for otb call default is 512
    :return: shaded snow file
    """

    condition_shaded_snow = "(im3b1 != 1) and (im2b1>=" + str(zs) + ") and (im4b1!=0) and ((im1b" + str(
        N_BLUE) + "-im1b" + str(N_NIR) + ")>" + str(shaded_snow_pass) + ")"

    shaded_snow_file = op.join(tmp_dir, SHADED_SNOW)

    logging.debug("Compute_shaded_snow condition : " + condition_shaded_snow)
    logging.debug("shaded_snow file: " + shaded_snow_file)

    band_math([img_vrt, dem, cloud_refine_file, relief_shadow_mask], shaded_snow_file + GDAL_OPT,
              condition_shaded_snow + "?1:0", ram)
    return shaded_snow_file


def compute_snow_pass3_vec(generic_snow_path, tmp_dir, generate_intermediate_vectors, use_gdal_trace_outline,
                           gdal_trace_outline_min_area, gdal_trace_outline_dp_toler):
    """
    Compute snow pass 3 as vector
    :param generic_snow_path: input mask
    :param tmp_dir: temp directory
    :param generate_intermediate_vectors: flag if vector should be generated
    :param use_gdal_trace_outline: Generate vector mask using gdal_trace_outline from gina_tools.
    :param gdal_trace_outline_min_area: Minimum area to keep in vector mask when using gdal_trace_outline
    :param gdal_trace_outline_dp_toler: Tolered pixel approximation in vector mask when using gdal_trace_outline
    (0 no approximation).
    :return: snow pass 3 file as vector.
    """
    snow_pass3_vec = op.join(tmp_dir, SNOW_PASS3_VEC)
    if generate_intermediate_vectors:
        polygonize(generic_snow_path, generic_snow_path, snow_pass3_vec, use_gdal_trace_outline,
                   gdal_trace_outline_min_area, gdal_trace_outline_dp_toler)
    return snow_pass3_vec


def compute_final_snow_vec(final_mask_file, tmp_dir, generate_vector, use_gdal_trace_outline,
                           gdal_trace_outline_min_area, gdal_trace_outline_dp_toler):
    """
    Compute snow mask vector.
    :param final_mask_file: input mask
    :param tmp_dir: temp directory
    :param generate_vector: Generate vector with snow and cloud masks of the final detection.
    :param use_gdal_trace_outline: Generate vector mask using gdal_trace_outline from gina_tools.
    :param gdal_trace_outline_min_area: Minimum area to keep in vector mask when using gdal_trace_outline
    :param gdal_trace_outline_dp_toler: Tolered pixel approximation in vector mask when using gdal_trace_outline
    (0 no approximation).
    :return:
    """
    final_snow_vec_file = op.join(tmp_dir, SNOW_VEC)
    if generate_vector:
        logging.debug("final_snow_vec_file : %s", final_snow_vec_file)
        logging.debug("final_mask_file : %s", final_mask_file)
        logging.debug("use_gdal_trace_outline : %s", use_gdal_trace_outline)
        logging.debug("gdal_trace_outline_min_area : %s", gdal_trace_outline_min_area)
        logging.debug("gdal_trace_outline_dp_toler : %s", gdal_trace_outline_dp_toler)
        polygonize(final_mask_file, final_mask_file, final_snow_vec_file, use_gdal_trace_outline,
                   gdal_trace_outline_min_area, gdal_trace_outline_dp_toler)
    return final_snow_vec_file


def compute_final_mask(cloud_refine_file, generic_snow_path, mask_back_to_cloud_file, no_data_mask_file, tmp_dir,
                       strict_cloud_mask, mode=MODE_SENTINEL2, ram=512):
    """
    Compute final mask
    :param cloud_refine_file: cloud refine file
    :param generic_snow_path: snow pass 3 file
    :param mask_back_to_cloud_file: mask back to cloud file
    :param no_data_mask_file: no data mask
    :param tmp_dir: temp directory
    :param strict_cloud_mask: strict cloud mask
    :param mode: mode default MODE_SENTINEL2
    :param ram: ram for otb call default 512
    :return: final snow mask
    """
    final_mask_file = op.join(tmp_dir, SNOW_MASK)

    if strict_cloud_mask:
        logging.debug("Strict cloud masking of snow pixels.")
        logging.debug("Only keep snow pixels which are not in the initial cloud mask in the final mask.")
        if mode == 'sen2cor':
            logging.debug("With sen2cor, strict cloud masking corresponds to the default configuration.")
        condition_snow = "(im2b1==1) and (im3b1==0)"
    else:
        condition_snow = "(im2b1==1)"

    condition_final = condition_snow + "?" + str(LABEL_SNOW) + ":((im1b1==1) or (im3b1==1))?" + str(LABEL_CLOUD) + ":0"

    logging.info("Final condition for snow masking: " + condition_final)

    band_math([cloud_refine_file, generic_snow_path, mask_back_to_cloud_file], final_mask_file,
              condition_final, ram)

    # Apply the no-data mask
    band_math([final_mask_file, no_data_mask_file], final_mask_file,
              "im2b1==1?" + str(LABEL_NO_DATA) + ":im1b1", ram)

    return final_mask_file


def compute_snow_pass3(snow_pass1_file, snow_pass2_file, tmp_dir, shaded_snow_file=None, ram=512):
    """
    Compute snow pass 3 : fusion of pass 1 and pass 2
    :param snow_pass1_file: snow pass 1 file
    :param snow_pass2_file: snow pass 2 file
    :param tmp_dir: temp directory
    :param shaded_snow_file: (optional) shaded snow file
    :param ram: ram for otb call default 512
    :return: snow pass 3 file
    """
    if snow_pass2_file is not None:
        if shaded_snow_file is not None:
            condition_pass3 = "(im3b1 == 1 or im1b1 == 1 or im2b1 == 1)"
            logging.debug("condition pass3 : %s", condition_pass3)
            snow_pass3_file = op.join(tmp_dir, SNOW_PASS3)
            logging.debug("snow_pass3_file : %s", snow_pass3_file)
            band_math([snow_pass1_file, snow_pass2_file, shaded_snow_file], snow_pass3_file + GDAL_OPT,
                      condition_pass3 + "?1:0", ram)
        else:
            condition_pass3 = "(im1b1 == 1 or im2b1 == 1)"
            logging.debug("condition pass3 : %s", condition_pass3)
            snow_pass3_file = op.join(tmp_dir, SNOW_PASS3)
            logging.debug("snow_pass3_file : %s", snow_pass3_file)
            band_math([snow_pass1_file, snow_pass2_file], snow_pass3_file + GDAL_OPT, condition_pass3 + "?1:0",
                      ram)
        generic_snow_path = snow_pass3_file
    else:
        generic_snow_path = snow_pass1_file
    logging.debug("generic_snow_path : %s", generic_snow_path)
    return generic_snow_path

def compute_uncalibrated_shaded_snow_mask(snow_pass1_file, snow_pass2_file, tmp_dir, shaded_snow_file, ram=512):
    """
    Compute uncalibrated shaded snow mask : 1 where shaded snow is 1 and snow pass 1 and snow pass 2 are 0
    :param snow_pass1_file: snow pass 1 file
    :param snow_pass2_file: snow pass 2 file
    :param tmp_dir: temp directory
    :param shaded_snow_file: shaded snow file
    :param ram: ram for otb call default 512
    :return: uncalibrated shaded snow mask
    """
    condition = "(im3b1 == 1 and im1b1 == 0 and im2b1 == 0)"
    logging.debug("condition uncalibrated shaded snow mask : %s", condition)
    uncalibrated_shaded_snow_file = op.join(tmp_dir, UNCALIBRATED_SHADED_SNOW)
    logging.debug("uncalibrated_shaded_snow_file : %s", uncalibrated_shaded_snow_file)
    band_math([snow_pass1_file, snow_pass2_file, shaded_snow_file], uncalibrated_shaded_snow_file + GDAL_OPT,
                condition + "?1:0", ram)
    return uncalibrated_shaded_snow_file

def compute_ndsi(img_vrt, final_mask_file, tmp_dir, ndsi_formula, ram=512):
    """
    Compude ndsi file.
    :param img_vrt: lis vrt
    :param final_mask_file: final mask file
    :param tmp_dir: tmp directory
    :param ndsi_formula: ndsi formula
    :param ram:  ram for otb call dafeult 512
    :return: ndsi file
    """
    # write NDSIx100 (0-100), nosnow (0) cloud (205) and nodata (255)
    ndsi_file = op.join(tmp_dir, NDSI)
    logging.debug("ndsi_file : %s", ndsi_file)
    expression = "(im2b1 == " + LABEL_SNOW + ")?100*" + str(ndsi_formula) + ":im2b1"
    logging.debug("expression : %s", expression)
    band_math([img_vrt, final_mask_file], ndsi_file, expression, ram)
    edit_nodata_value(ndsi_file, nodata_value=int(LABEL_NO_DATA))
    return ndsi_file


def compute_fsc_toc(ndsi_file, final_mask_file, tmp_dir, fscToc_Eq, ram=512):
    """
    Compute fsc toc : write top-of-canopy FSC (0-100), nosnow (0) cloud (205) and nodata (255)
    ~ self.fscToc_Eq="1.45*ndsi-0.01"
    :param ndsi_file: ndsi file
    :param final_mask_file: final mask file
    :param tmp_dir: tmp directory
    :param fscToc_Eq: fsc toc equation
    :param ram: ram for otb call default 512
    :return: fsc toc file
    """
    eq = "min(" + str(fscToc_Eq) + ",1)"
    logging.debug("eq : %s", eq)
    exp = eq.replace("ndsi", "im1b1/100")  # ndsi was written in %
    logging.debug("exp : %s", exp)
    expression = "(im2b1 == " + LABEL_SNOW + ") ? 100*" + exp + " : im2b1"
    logging.debug("expression : %s", expression)
    fscToc_file = op.join(tmp_dir, FSCTOC)
    band_math([ndsi_file, final_mask_file], fscToc_file, expression, ram)
    edit_nodata_value(fscToc_file, nodata_value=int(LABEL_NO_DATA))
    return fscToc_file


def adjust_for_hillshade(uncalibrated_shaded_snow, fsc_toc_file, tmp_dir, ram):
    """
    Adjust FSC for hill shade : uncalibrated_shaded_snow == 1 => FSC := 100
    :param uncalibrated_shaded_snow: mask for uncalibrated shaded snow
    :param fsc_toc_file: fsc file to adjust
    :param tmp_dir: tmp directory
    :param ram: ram for otb call default 512
    :return: fsc toc file adjusted for hill shade
    """
    expression = "(im1b1 == 1) ? 100 : im2b1 "
    logging.debug("expression : %s", expression)
    fscTocHS_file = op.join(tmp_dir, FSCTOCHS)
    band_math([uncalibrated_shaded_snow, fsc_toc_file], fscTocHS_file, expression, ram)
    return fscTocHS_file


def compute_fsc_og(name, fscToc_file, tcd_file, final_mask_file, output_dir, fscOg_Eq, ram=512):
    """
        Compute fsc toc : write on-ground FSC (0-100), nosnow (0) cloud (205) and nodata (255)
         ~ self.fscOg_Eq="fscToc/(1-tcd)"
        :param name: file name
        :param fscToc_file: fscToc file
        :param tcd_file: tcd file
        :param final_mask_file: final mask file
        :param output_dir: output directory
        :param fscOg_Eq: fsc og equation
        :param ram: ram for otb call default 512
        :return: fsc toc file
        """
    if tcd_file is not None:
        eq = "min(" + str(fscOg_Eq) + ",1)"
        logging.debug("eq : %s", eq)
        exp = eq.replace("fscToc", "im1b1/100")  # fscToc was written in %
        logging.debug("exp : %s", exp)
        exp = exp.replace("tcd", "im3b1/100")  # tcd is given in %
        expression = "(im2b1 == " + LABEL_SNOW + ") ? ( im3b1 > 100 ? im1b1 : 100*" + exp + " ) : im2b1"
        logging.debug("expression : %s", expression)
        fscOg_file = op.join(output_dir, name)
        band_math([fscToc_file, final_mask_file, tcd_file], fscOg_file, expression, ram)
        edit_nodata_value(fscOg_file, nodata_value=int(LABEL_NO_DATA))
        return fscOg_file
    else:
        logging.warning("Tree cover density file is not defined, FSC on ground can not be computed.")
        return None


def create_metadata(final_mask_file, output_dir, product_id, zs):
    """
    Create metadata file
    :param final_mask_file: final mask
    :param output_dir: output dire
    :param product_id: product id
    :param zs: zs
    :return: metadata file
    """
    # Compute and create the content for the product metadata file.
    snow_percent = compute_percent(final_mask_file, LABEL_SNOW, LABEL_NO_DATA)
    logging.info("Snow percent = " + str(snow_percent))

    cloud_percent = compute_percent(final_mask_file, LABEL_CLOUD, LABEL_NO_DATA)
    logging.info("Cloud percent = " + str(cloud_percent))

    root = etree.Element("Source_Product")
    etree.SubElement(root, "PRODUCT_ID").text = product_id
    etree.SubElement(root, "DOI").text = DOI_URL
    egil = etree.SubElement(root, "Global_Index_List")
    etree.SubElement(egil, "QUALITY_INDEX", name='ZS').text = str(zs)
    etree.SubElement(
        egil,
        "QUALITY_INDEX",
        name='SnowPercent').text = str(snow_percent)
    etree.SubElement(
        egil,
        "QUALITY_INDEX",
        name='CloudPercent').text = str(cloud_percent)
    et = etree.ElementTree(root)
    metadata_file = op.join(output_dir, METADATA)
    et.write(metadata_file, pretty_print=True)
