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

import glob
import json
import logging
import os
import os.path as op
import subprocess
import uuid
import re
from datetime import datetime
from datetime import timedelta
from distutils import spawn

import numpy as np

from osgeo import gdal, gdalconst


# OTB Applications
# Import python decorators for the different needed OTB applications

# USED
def call_subprocess(cmd):
    """ Run subprocess and write to stdout and stderr
    """
    logging.info("Running: " + " ".join(cmd))
    try:
        process = subprocess.run(cmd, check=True)
        logging.info(process.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(e)
        raise e


def str_to_datetime(date_string, format="%Y%m%d"):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date_string)
    return datetime.strptime(date_string, format)


def datetime_to_str(date, format="%Y%m%d"):
    """ Return the datetime corresponding to the input string
    """
    logging.debug(date)
    return date.strftime(format)


def write_list_to_file(filename, str_list):
    """ Write in a file a list of string as separate lines
    """
    output_file = open(filename, "w")
    output_file.write("\n".join(str_list))
    output_file.close()


def read_list_from_file(filename):
    """ Read file lines as a list of string removing end-of-line delimiters
    """
    output_file = open(filename, "r")
    lines = output_file.readlines()
    output_file.close()
    return [line.rstrip() for line in lines]

def find_file(folder, pattern):
    """ Search recursively into a folder to find a pattern match
    """
    logging.debug("folder :%s", folder)
    logging.debug("pattern :%s", pattern)
    match = None

    for root, dirs, files in os.walk(folder):
        for file in files:
            if re.match(pattern, file):
                logging.debug("match file :%s", file)
                match = os.path.join(root, file)
                break

    return match

def polygonize(input_img, input_mask, output_vec, use_gina, min_area, dp_toler):
    """Helper function to polygonize raster mask using gdal polygonize

    if gina-tools is available it use gdal_trace_outline instead of
    gdal_polygonize (faster)
    """
    # Test if gdal_trace_outline is available
    gdal_trace_outline_path = spawn.find_executable("gdal_trace_outline")
    if not use_gina:
        # Use gdal_polygonize
        logging.info("Use gdal_polygonize to polygonize raster mask...")
        call_subprocess([
            "gdal_polygonize.py", input_img,
            "-f", "ESRI Shapefile",
            "-mask", input_mask, output_vec])
    elif use_gina and (gdal_trace_outline_path is None):
        logging.error("Cannot use gdal_trace_outline, executable not found on system!")
        logging.error("The vector file will not be generated.")
        logging.error("You can either disable the use_gdal_trace_outline option or install the tools")
    else:
        logging.info("Use gdal_trace_outline to polygonize raster mask...")

        # Temporary file to store result of outline tool
        # Get unique identifier for the temporary file
        # Retrieve directory from input vector file
        input_dir = os.path.dirname(output_vec)
        unique_filename = uuid.uuid4()
        tmp_poly = op.join(input_dir, str(unique_filename))

        tmp_poly_shp = tmp_poly + ".shp"
        # We can use here gina-tools gdal_trace_outline which is faster
        command = [
            "gdal_trace_outline",
            input_img,
            "-classify",
            "-out-cs",
            "en",
            "-ogr-out",
            tmp_poly_shp,
            "-dp-toler",
            str(dp_toler),
            "-split-polys"]
        if min_area:
            command.extend(["-min-ring-area", str(min_area)])
        call_subprocess(command)

        # Then remove polygons with 0 as field value and rename field from
        # "value" to "DN" to follow same convention as gdal_polygonize
        call_subprocess([
            "ogr2ogr",
            "-sql",
            'SELECT value AS SEB from \"' +
            str(unique_filename) +
            '\" where value != 0',
            output_vec,
            tmp_poly_shp])

        # Remove temporary vectors
        for shp in glob.glob(tmp_poly + "*"):
            os.remove(shp)


def edit_nodata_value(raster_file, nodata_value=None, bands=None):
    ds = gdal.Open(raster_file, gdal.GA_Update)

    # iterate on each band
    for band_no in range(1, ds.RasterCount + 1):

        if bands is not None:
            if band_no not in bands:
                # this band was not specified for edition, skip
                continue

        band = ds.GetRasterBand(band_no)
        if nodata_value is None:
            # remove nodata value
            ds.GetRasterBand(band_no).DeleteNoDataValue()
        else:
            # change nodata value
            ds.GetRasterBand(band_no).SetNoDataValue(nodata_value)


def edit_raster_from_shapefile(raster_target, src_shapefile, applied_value=0):
    shape_mask = ogr.Open(src_shapefile)
    ds = gdal.Open(raster_target, gdal.GA_Update)
    for shape_mask_layer in shape_mask:
        gdal.RasterizeLayer(ds, [1], shape_mask_layer, burn_values=[applied_value])


def edit_raster_from_raster(target_raster, src_raster, src_values, applied_value=0, layered_processing=False):
    ds_mask = gdal.Open(src_raster, gdal.GA_ReadOnly)
    band_mask = ds_mask.GetRasterBand(1)
    ds = gdal.Open(target_raster, gdal.GA_Update)
    band = ds.GetRasterBand(1)

    if band.XSize != band_mask.XSize or band.YSize != band_mask.YSize:
        msg = 'array sizes from files do not match:\n%s' % (
            '\n'.join([' - %s' % el for el in [target_raster, src_raster]]))
        logging.error(msg)
        raise IOError(msg)

    if layered_processing:
        # iterate load line per line to avoid memory issues
        for ii in range(band.YSize - 1, -1, -1):
            data = band.ReadAsArray(xoff=0, yoff=ii, win_xsize=band.XSize, win_ysize=1, buf_xsize=band.XSize,
                                    buf_ysize=1)
            data_mask = band_mask.ReadAsArray(xoff=0, yoff=ii, win_xsize=band.XSize, win_ysize=1, buf_xsize=band.XSize,
                                              buf_ysize=1)
            for val in src_values:
                data[data_mask == val] = applied_value
            band.WriteArray(data, xoff=0, yoff=ii)
    else:
        data = band.ReadAsArray()
        data_mask = band_mask.ReadAsArray()
        for val in src_values:
            data[data_mask == val] = applied_value
        band.WriteArray(data)


def get_raster_as_array(raster_file_name):
    """ Open image file as numpy array using gdal
    """
    dataset = gdal.Open(raster_file_name, gdalconst.GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray()
    return array


def compute_percent(image_path, value, no_data=-10000):
    """
     Compute the occurrence of value as percentage in the input image
    :param image_path: input image
    :param value: researched value
    :param no_data: no data value default is -10000
    :return: percentage of researched value in the input image
    """
    array_image = get_raster_as_array(image_path)
    tot_pix = array_image.size
    if no_data is not None:
        tot_pix = np.sum(array_image != int(no_data))

    if tot_pix != 0:
        count_pix = np.sum(array_image == int(value))
        return (float(count_pix) / float(tot_pix)) * 100
    else:
        return 0


class JSONCustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return datetime_to_str(o)
        elif isinstance(o, timedelta):
            return o.days
        return super().default(o)
