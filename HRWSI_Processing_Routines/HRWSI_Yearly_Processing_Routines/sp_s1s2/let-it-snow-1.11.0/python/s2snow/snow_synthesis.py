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
from datetime import datetime
import logging
import os
import os.path as op
import shutil
from datetime import timedelta

from osgeo import gdal
# OTB Applications
from lxml import etree

from otbApplication import ImagePixelType_uint8, ImagePixelType_uint16

# Import python decorators for the different needed OTB applications
from s2snow.compute_NOBS import compute_NOBS
from s2snow.compute_NSP import compute_NSP
from s2snow.compute_SOD_SMOD import compute_SOD_SMOD
from s2snow.lis_constant import TMP_DIR, OUTPUT_DATES_FILE, DOI_URL
from s2snow.lis_exception import NoProductMatchingSynthesis
from s2snow.otb_wrappers import band_math, super_impose, band_mathX, gap_filling, get_app_output
from s2snow.snow_product import SnowProduct
from s2snow.utils import datetime_to_str
from s2snow.utils import write_list_to_file, read_list_from_file

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
from importlib.metadata import version

GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

LABEL_NO_SNOW = "0"
LABEL_SNOW = "100"
LABEL_CLOUD = "205"
LABEL_NO_DATA = "255"
LABEL_NO_DATA_OLD = "254"


def compute_snow_synthesis(config, output_dir, h2_chain_version=None, product_counter=None):
    tmp_dir = os.path.join(output_dir, TMP_DIR)

    # manage synthesis name
    synthesis_name = config.synthesis_id
    if h2_chain_version is not None:
        synthesis_name = synthesis_name + "_" + h2_chain_version
    else:
        synthesis_name = synthesis_name + "_" + version('s2snow')
    if product_counter is not None:
        synthesis_name = synthesis_name + "_" + product_counter

    logging.info("Load S2 snow products.")
    product_dict = load_snow_products(config.date_start, config.date_stop, config.date_margin,
                                      config.input_products_list, config.tile_id, tmp_dir)

    # Exiting with error if none of the input products were loaded
    if not product_dict:
        msg = "No product matching synthesis definition found."
        logging.error(msg)
        raise NoProductMatchingSynthesis(msg)

    # Do the loading of the products to densify the timeserie
    if config.densification_products_list:
        logging.info("Load densification products.")
        load_densification_products(config.date_margin, config.date_start, config.date_stop,
                                    config.densification_products_list, tmp_dir, product_dict, config.ram)
        synthesis_name = "LIS_S2L8-SNOW-{}_" + synthesis_name + ".tif"
    else:
        synthesis_name = "LIS_S2-SNOW-{}_" + synthesis_name + ".tif"

    # ----------------------------------------------------------------------------------------
    # Sort products by acquisition date, retrieve input and output dates
    # ----------------------------------------------------------------------------------------
    logging.info("Sort products by acquisition date.")
    # re-order products according acquisition date
    input_dates_file_path = op.join(tmp_dir, "input_dates.txt")
    input_dates = sorted(product_dict.keys())
    write_list_to_file(input_dates_file_path, input_dates)

    # compute or retrieve the output dates
    logging.info("Retrieve output dates.")
    output_dates_filename = config.output_dates_filename
    if output_dates_filename is not None and op.exists(output_dates_filename):
        logging.debug("Read output_date_file : %s", output_dates_filename)
        output_dates = read_list_from_file(output_dates_filename)
    else:
        output_dates_filename = os.path.join(tmp_dir, OUTPUT_DATES_FILE)
        output_dates = compute_output_dates(config.date_start, config.date_stop, output_dates_filename)

    # ----------------------------------------------------------------------------------------
    # Merge products at the same date
    # ----------------------------------------------------------------------------------------
    logging.info("Merge products at the same date.")
    merged_product_dict = merge_product_at_same_date(tmp_dir, product_dict, config.ram)

    # ----------------------------------------------------------------------------------------
    # Convert snow masks into binary masks
    # ----------------------------------------------------------------------------------------
    logging.info("Convert snow masks into snow and cloud binary snow masks.")
    binary_snow_mask_list = convert_snow_masks_into_binary_snow_masks(tmp_dir, config.ram, merged_product_dict)
    binary_cloud_mask_list = convert_snow_masks_into_binary_cloud_masks(tmp_dir, config.ram, merged_product_dict)

    # ----------------------------------------------------------------------------------------
    # Compute Cloud Coverage Duration "CLOUD_OCCURENCE" and multitemp_cloud_mask
    # ----------------------------------------------------------------------------------------
    logging.info("Compute multitemp cloud vrt")
    multitemp_cloud_vrt = build_cloud_mask_vrt(tmp_dir, binary_cloud_mask_list)

    logging.info("Compute cloud occurence")
    compute_CCD(tmp_dir, binary_cloud_mask_list, multitemp_cloud_vrt, config.synthesis_id,
                config.ram)

    # ----------------------------------------------------------------------------------------
    # Compute Snow Coverage Duration "SCD" and multitemp_snow_mask
    # ----------------------------------------------------------------------------------------
    logging.info("Compute snow vrt")
    multitemp_snow_vrt = build_snow_mask_vrt(tmp_dir, binary_snow_mask_list)
    multitemp_snow100 = build_multitemp_snow100(tmp_dir, multitemp_snow_vrt, config.ram)
    logging.info("Compute gapfilled timeserie")
    gapfilled_timeserie = build_gapfilled_timeserie(tmp_dir, multitemp_snow100, multitemp_cloud_vrt,
                                                    input_dates_file_path, output_dates_filename,
                                                    config.synthesis_id, config.ram)
    logging.info("Compute snow coveration duration")
    compute_SCD(output_dir, output_dates, gapfilled_timeserie, synthesis_name, config.ram)

    # run compute SOD_SMOD
    logging.info("Compute SOD and SMOD")
    compute_SOD_SMOD(gapfilled_timeserie, synthesis_name=synthesis_name, output_dir=output_dir)

    # run compute NOBS
    logging.info("Compute NOBS")
    compute_NOBS(multitemp_cloud_vrt, synthesis_name=synthesis_name, output_dir=output_dir)

    # run compute NSP
    logging.info("Compute NSP")
    compute_NSP(gapfilled_timeserie, synthesis_name=synthesis_name, output_dir=output_dir)

    # create metadata
    logging.info("Create metadata")
    create_snow_annual_map_metadata(config.input_products_list + config.densification_products_list, output_dir)


def build_snow_mask_vrt(tmp_dir, binary_snow_mask_list):
    logging.debug("build_snow_mask_vrt")
    logging.debug("binary_snow_mask_list : %s", str(binary_snow_mask_list))
    logging.debug("tmp_dir : %s", str(tmp_dir))

    multitemp_snow_vrt = op.join(tmp_dir, "multitemp_snow_mask.vrt")

    # build cloud mask vrt
    gdal.BuildVRT(multitemp_snow_vrt,
                  binary_snow_mask_list,
                  separate=True,
                  srcNodata='None')

    return multitemp_snow_vrt


def build_multitemp_snow100(tmp_dir, multitemp_snow_vrt, ram):
    logging.debug("build_multitemp_snow100")
    logging.debug("multitemp_snow_vrt : %s", str(multitemp_snow_vrt))
    logging.debug("tmp_dir : %s", str(tmp_dir))
    logging.debug("ram : %s",  str(ram))
    multitemp_snow100 = op.join(tmp_dir, "multitemp_snow100.tif")
    
    # multiply by 100 for the temporal interpolation
    logging.debug("Scale by 100 multitemp snow mask vrt")
    bandMathXApp = band_mathX([multitemp_snow_vrt],
                              multitemp_snow100,
                              "im1 mlt 100",
                              ram,
                              ImagePixelType_uint8)
    
    bandMathXApp.ExecuteAndWriteOutput()
    bandMathXApp = None
    return multitemp_snow100


def create_snow_annual_map_metadata(product_list, output_dir):
    # Compute and create the content for the product metadata file.
    logging.debug("create_snow_annual_map_metadata")
    logging.debug("product_list : ")
    for product in product_list:
        logging.debug("product : %s", str(product))
    logging.debug("output_dir : %s", str(output_dir))
    metadata_path = op.join(output_dir, "LIS_METADATA.XML")
    logging.info("Metadata file: %s", metadata_path)
    root = etree.Element("METADATA")
    etree.SubElement(root, "DOI").text = DOI_URL
    input_lst = etree.SubElement(root, "INPUTS_LIST")
    for product_path in product_list:
        logging.debug("Product path: {}".format(product_path))
        product_name = op.basename(str(product_path))
        etree.SubElement(input_lst, "PRODUCT_NAME").text = product_name
    et = etree.ElementTree(root)
    et.write(metadata_path, pretty_print=True)


def build_gapfilled_timeserie(tmp_dir, multitemp_snow100, multitemp_cloud_vrt, input_dates_filename,
                              output_dates_filename, synthesis_id, ram):
    logging.debug("build_multitemp_snow100_gapfilled")
    logging.debug("tmp_dir : %s", str(tmp_dir))
    logging.debug("multitemp_snow100 : %s", str(multitemp_snow100))
    logging.debug("multitemp_cloud_vrt : %s", str(multitemp_cloud_vrt))
    logging.debug("input_dates_filename : %s", str(input_dates_filename))
    logging.debug("output_dates_filename : %s", str(output_dates_filename))
    logging.debug("ram : %s", str(ram))

    multitemp_snow100_gapfilled = op.join(tmp_dir, "multitemp_snow100_gapfilled.tif")
    gapfilled_timeserie = op.join(tmp_dir, "DAILY_SNOW_MASKS_" + synthesis_id + ".tif")

    app_gap_filling = gap_filling(multitemp_snow100,
                                  multitemp_cloud_vrt,
                                  multitemp_snow100_gapfilled + "?&gdal:co:COMPRESS=DEFLATE",
                                  input_dates_filename,
                                  output_dates_filename,
                                  ram,
                                  ImagePixelType_uint8)
    app_gap_filling

    # @TODO the mode is for now forced to DEBUG in order to generate img on disk
    # img_in = get_app_output(app_gap_filling, "out", mode)
    # if mode == "DEBUG":
    # shutil.copy2(gapfilled_timeserie, path_out)
    # app_gap_filling = None
    img_in = get_app_output(app_gap_filling, "out", "DEBUG")
    app_gap_filling = None
    # threshold to 0 or 1
    logging.info("Round to binary series of snow occurrence")
    bandMathXApp = band_mathX([img_in],
                              gapfilled_timeserie + GDAL_OPT,
                              "(im1 mlt 2) dv 100",
                              ram,
                              ImagePixelType_uint8)
    bandMathXApp.ExecuteAndWriteOutput()
    bandMathXApp = None

    return gapfilled_timeserie


def compute_SCD(output_dir, output_dates, gapfilled_timeserie, synthesis_name, ram):
    logging.debug("compute_SCD")
    logging.debug("output_dates : %s ", str(output_dates))
    logging.debug("output_dir : %s", str(output_dir))
    logging.debug("gapfilled_timeserie : %s", str(gapfilled_timeserie))
    logging.debug("synthesis_name : %s", str(synthesis_name))
    logging.debug("ram : %s", str(ram))

    # generate the annual map
    snow_coverage_duration = op.join(output_dir, synthesis_name.format("SCD"))
    band_index = list(range(1, len(output_dates) + 1))
    logging.debug("Bande index: %s", str(band_index))
    expression = "+".join(["im1b" + str(i) for i in band_index])
    logging.debug("expression: %s", expression)
    band_math([gapfilled_timeserie], snow_coverage_duration + "?&gdal:co:COMPRESS=DEFLATE", expression, ram, ImagePixelType_uint16)
    return snow_coverage_duration


def build_cloud_mask_vrt(tmp_dir, binary_cloud_mask_list):
    logging.debug("build_cloud_mask_vrt")
    logging.debug("binary_cloud_mask_list : %s", str(binary_cloud_mask_list))
    logging.debug("tmp_dir : %s", str(tmp_dir))

    multitemp_cloud_vrt = op.join(tmp_dir, "multitemp_cloud_mask.vrt")

    # build cloud mask vrt
    gdal.BuildVRT(multitemp_cloud_vrt,
                  binary_cloud_mask_list,
                  separate=True,
                  srcNodata='None')

    return multitemp_cloud_vrt


def compute_CCD(tmp_dir, binary_cloud_mask_list, multitemp_cloud_vrt, synthesis_id, ram=512):
    logging.debug("compute_CCD")
    logging.debug("binary_cloud_mask_list : %s", str(binary_cloud_mask_list))
    logging.debug("tmp_dir : %s", str(tmp_dir))
    logging.debug("synthesis_id : %s", str(synthesis_id))
    logging.debug("ram : %s", str(ram))

    ccd_file_path = op.join(tmp_dir, "CLOUD_OCCURENCE_" + synthesis_id + ".tif")

    # generate the summary map
    band_index = list(range(1, len(binary_cloud_mask_list) + 1))
    logging.debug("bande index : %s",str(band_index))
    expression = "+".join(["im1b" + str(i) for i in band_index])
    logging.debug("expression : %s", expression)
    band_math([multitemp_cloud_vrt],
                            ccd_file_path,
                            expression,
                            ram,
                            ImagePixelType_uint16)

    return ccd_file_path


def convert_snow_masks_into_binary_cloud_masks(path_out, ram, product_dict):
    logging.debug("convert_snow_masks_into_binary_cloud_masks")
    logging.debug("path_out : %s", str(path_out))
    logging.debug("product_dict : %s", str(product_dict))
    logging.debug("ram : %s", str(ram))

    # convert the snow masks into binary cloud masks
    expression = "im1b1==" + LABEL_CLOUD + "?1:(im1b1==" + LABEL_NO_DATA + "?1:(im1b1==" + LABEL_NO_DATA_OLD + "?1:0))"
    binary_cloud_mask_list = convert_mask_list(path_out, product_dict, expression, "cloud", ram,
                                               mask_format=GDAL_OPT)
    logging.debug("Binary cloud mask list:")
    logging.debug(binary_cloud_mask_list)
    return binary_cloud_mask_list


def convert_snow_masks_into_binary_snow_masks(path_out, ram, product_dict):
    logging.debug("convert_snow_masks_into_binary_snow_masks")
    logging.debug("path_out : %s", str(path_out))
    logging.debug("product_dict : %s", str(product_dict))
    logging.debug("ram : %s", str(ram))

    # convert the snow masks into binary snow masks
    #expression = "(im1b1==" + LABEL_SNOW + ")?1:0"
    expression = "(im1b1>0 and im1b1<=" + LABEL_SNOW + ")?1:0"
    binary_snow_mask_list = convert_mask_list(path_out, product_dict, expression, "snow", ram,
                                              mask_format=GDAL_OPT)
    logging.debug("Binary snow mask list:")
    logging.debug(binary_snow_mask_list)
    return binary_snow_mask_list


def merge_product_at_same_date(path_out, product_dict, ram):
    logging.debug("merge_product_at_same_date")
    logging.debug("path_out : %s", str(path_out))
    logging.debug("product_dict : %s", str(product_dict))
    logging.debug("ram : %s", str(ram))

    merge_product_dict = {}
    for key in list(product_dict.keys()):
        if len(product_dict[key]) > 1:
            merged_mask = op.join(path_out, key + "_merged_snow_product.tif")
            merge_masks_at_same_date(product_dict[key],
                                     merged_mask,
                                     LABEL_SNOW,
                                     ram)
            merge_product_dict[key] = merged_mask
        else:
            merge_product_dict[key] = product_dict[key][0].get_snow_mask()
        logging.debug("snow mask : %s", str(merge_product_dict[key]))

    return merge_product_dict


def compute_output_dates(date_start, date_stop, output_dates_filename):
    logging.debug("compute_output_dates")
    logging.debug("date_start : %s", str(date_start))
    logging.debug("date_stop : %s", str(date_stop))
    logging.debug("output_dates_filename : %s", str(output_dates_filename))
    output_dates = []
    logging.debug("Compute output_dates from {} to {}".format(date_start, date_stop))
    tmp_date = date_start
    while tmp_date <= date_stop:
        output_dates.append(datetime_to_str(tmp_date))
        tmp_date += timedelta(days=1)
    write_list_to_file(output_dates_filename, output_dates)
    return output_dates


def load_densification_products(date_margin, date_start, date_stop, densification_products_list, path_tmp, product_dict,
                                ram):
    logging.debug("load_densification_products")
    logging.debug("date_margin : %s", str(date_margin))
    logging.debug("date_start : %s", str(date_start))
    logging.debug("date_stop : %s", str(date_stop))
    logging.debug("densification_products_list :")
    for product in densification_products_list:
        logging.debug("product : %s", str(product))
    logging.debug("path_tmp : %s", str(path_tmp))
    logging.debug("product_dict :")
    for product in product_dict.values():
        logging.debug("product : %s", str(product))
    logging.debug("ram : %s", str(ram))

    # load densification snow products
    densification_product_dict = load_snow_products(date_start, date_stop, date_margin, densification_products_list, None, path_tmp)
    logging.debug("Densification product dict:")
    logging.debug(densification_product_dict)

    # Get the footprint of the first snow product
    s2_footprint_ref = product_dict[list(product_dict.keys())[0]][0].get_snow_mask()

    if densification_product_dict:
        # Reproject the densification products on S2 tile before going further
        logging.debug("Densification product reprojections on S2 tile.")
        for densifier_product_key in list(densification_product_dict.keys()):
            for densifier_product in densification_product_dict[densifier_product_key]:
                original_mask = densifier_product.get_snow_mask()
                reprojected_mask = op.join(path_tmp,
                                           densifier_product.product_name + "_reprojected.tif")
                if not os.path.exists(reprojected_mask):
                    super_impose_app = super_impose(s2_footprint_ref,
                                                    original_mask,
                                                    reprojected_mask,
                                                    "nn",
                                                    int(LABEL_NO_DATA),
                                                    ram,
                                                    ImagePixelType_uint8)
                    super_impose_app.ExecuteAndWriteOutput()
                    super_impose_app = None
                densifier_product.snow_mask = reprojected_mask
                logging.debug(densifier_product.snow_mask)

            # Add the products to extend the product_dict
            if densifier_product_key in list(product_dict.keys()):
                product_dict[densifier_product_key].extend(densification_product_dict[densifier_product_key])
            else:
                product_dict[densifier_product_key] = densification_product_dict[densifier_product_key]

            logging.debug(product_dict[densifier_product_key])
    else:
        logging.warning("No Densifying candidate product found!")


def load_snow_products(date_start, date_stop, date_margin, snow_products_list, tile_id, path_tmp):
    logging.debug("load_products")
    logging.debug("date_start : %s", str(date_start))
    logging.debug("date_stop : %s", str(date_stop))
    logging.debug("date_margin : %s", str(date_margin))
    if tile_id is not None:
        logging.debug("tile_id : %s", tile_id) 

    # init result snow product dict
    s2_snow_products = {}
    search_start_date = date_start - date_margin
    search_stop_date = date_stop + date_margin

    for product_path in snow_products_list:
        logging.debug("product_path : %s", str(product_path))
        try:
            product = SnowProduct(str(product_path), path_tmp)
        except Exception as e:
            logging.debug("exception raised:", str(e))
            raise e
            
        logging.debug("product : %s", str(product))

        acquisition_day = datetime.strftime(product.acquisition_date, "%Y%m%d")
        should_be_used_in_synthesis = True
        if search_start_date > product.acquisition_date or \
                search_stop_date < product.acquisition_date:
            should_be_used_in_synthesis = False
            logging.warning("Discarding product : {}, because acquisition date : {} is not in the synthesis "
                            "period : {} - {}".format(str(product_path), str(product.acquisition_date),
                                                      str(search_start_date), str(search_stop_date)))
        if (tile_id is not None) and (tile_id not in product.tile_id):
            should_be_used_in_synthesis = False
            logging.warning("Discarding product : {}, because product tile : {} does not correspond to "
                            "synthesis tile : {}".format(str(product_path), str(product.tile_id), str(tile_id)))

        if should_be_used_in_synthesis:
            if acquisition_day not in list(s2_snow_products.keys()):
                # first product for this date
                s2_snow_products[acquisition_day] = [product]
            else:
                s2_snow_products[acquisition_day].append(product)
            logging.info("Keeping product : %s",str(product))

    logging.debug("S2 snow products dictionary:")

    return s2_snow_products


def convert_mask_list(path_tmp, product_dict, expression, type_name, ram, mask_format=""):
    logging.debug("convert_mask_list")
    logging.debug("path_tmp : %s", path_tmp)
    logging.debug("product_dict : ")
    for s_mask in product_dict.values():
        logging.debug(s_mask)
    logging.debug("expression : %s", expression)
    logging.debug("type_name : %s", type_name)
    logging.debug("ram : %s", str(ram))
    logging.debug("mask_format : %s", mask_format)

    binary_mask_list = []
    for mask_date in sorted(product_dict):
        binary_mask = op.join(path_tmp,
                              mask_date + "_" + type_name + "_binary.tif")
        binary_mask = extract_binary_mask(product_dict[mask_date],
                                          binary_mask,
                                          expression,
                                          ram,
                                          mask_format)
        binary_mask_list.append(binary_mask)
    return binary_mask_list


def extract_binary_mask(mask_in, mask_out, expression, ram, mask_format=""):
    logging.debug("extract_binary_mask")
    logging.debug("mask_in : %s", mask_in)
    logging.debug("mask_out : %s", mask_out)
    logging.debug("expression : %s", expression)
    logging.debug("ram : %s", str(ram))
    logging.debug("mask_format : %s", mask_format)

    band_math([mask_in], mask_out + mask_format, expression, ram, ImagePixelType_uint8)
    return mask_out


def merge_masks_at_same_date(snow_product_list, merged_snow_product, threshold=100, ram=None):
    """ This function implement the fusion of multiple snow mask

    Keyword arguments:
    snow_product_list -- the input mask list
    merged_snow_product -- the output filepath
    threshold -- the threshold between valid <= invalid data
    ram -- the ram limitation (not mandatory)
    """
    logging.debug("merge_masks_at_same_date")
    logging.debug("snow_product_list ----- ")
    for snow_product in snow_product_list:
        logging.debug("snow_product : %s", str(snow_product))
    logging.debug("merged_snow_product : %s", merged_snow_product)
    logging.debug("threshold : %s", threshold)
    logging.debug("ram : %s", str(ram))

    # the merging is performed according the following selection:
    #   if img1 < threshold use img1 data
    #   else if img2 < threshold use img2 data
    #   else if imgN < threshold use imgN data
    # the order of the images in the input list is important:
    #   we expect to have first the main input products
    #   and then the densification products
    img_index = list(range(1, len(snow_product_list) + 1))
    expression_merging = "".join(["(im" + str(i) + "b1<=" + str(threshold) + "?im" + str(i) + "b1:" for i in img_index])
    expression_merging += "im" + str(img_index[-1]) + "b1"
    expression_merging += "".join([")" for i in img_index])

    img_list = [i.get_snow_mask() for i in snow_product_list]
    band_math(img_list, merged_snow_product, expression_merging, ram, ImagePixelType_uint8)

