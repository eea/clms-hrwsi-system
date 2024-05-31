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

import rasterio
import numpy as np
import itertools, operator, sys, os
import logging
from importlib.metadata import version


def compute_SOD_SMOD(input_file, synthesis_name=None, output_dir=None):
    """
    Computes the snow onset date (SOD) and the snow melt-out date (SMOD) from a stack of daily snow maps.
    The dates are given in number of days since the first day of the synthesis (usually September 01).
    :param output_dir : output directory
    :param input_file: the interpolated daily raster generated using run_show_annual_map script.
    :param synthesis_name: synthesis_name
    :return:
    """
    logging.info("Start compute_SOD_SMOD.py using: {}".format(input_file))
    logging.debug("compute_SOD_SMOD")
    logging.debug("tmp_dir : %s", output_dir)
    logging.debug("input_file : %s", input_file)
    logging.debug("synthesis_name : %s", synthesis_name.format("XXX"))

    if not os.path.isfile(input_file):
        msg = "Input file does not exist : {}".format(input_file)
        logging.error(msg)
        raise IOError(msg)

    if output_dir is None:
        output_dir = os.path.split(input_file)[0]
    if synthesis_name is None:
        synthesis_id = os.path.split(input_file)[1]
        sod_file = os.path.join(output_dir, "LIS_SNOW-SOD_{}.tif".format(synthesis_id))
        smod_file = os.path.join(output_dir, "LIS_SNOW-SMOD_{}.tif".format(synthesis_id))
    else:
        sod_file = os.path.join(output_dir, synthesis_name.format("SOD"))
        smod_file = os.path.join(output_dir, synthesis_name.format("SMOD"))

    src = rasterio.open(input_file, 'r')
    n = src.meta["count"]

    W = src.read(range(1, n + 1))
    n = np.shape(W)[1]
    m = np.shape(W)[2]
    sod = np.zeros((n, m), dtype='uint16')
    smod = np.zeros((n, m), dtype='uint16')
    for i in range(0, n):
        for j in range(0, m):
            w = W[:, i, j]
            if np.sum(w) > 10:
                r = max((list(y) for (x, y) in itertools.groupby((enumerate(w)), operator.itemgetter(1)) if x == 1),
                        key=len)
                smod[i, j] = r[-1][0]
                sod[i, j] = r[0][0]

    with rasterio.Env():
        profile = src.profile
        profile.update(
            dtype=rasterio.uint16,
            compress='deflate',
            count=1)

        with rasterio.open(smod_file, 'w', **profile) as dst:
            dst.write(smod.astype(rasterio.uint16), 1)

        with rasterio.open(sod_file, 'w', **profile) as dst:
            dst.write(sod.astype(rasterio.uint16), 1)



def show_help():
    """
    Show help for compute_SOD_SMOD .
    :return:
    """
    print("This script is used to compute SOD and SMOD. " \
          + "Input file is the interpolated daily raster generated using run_show_annual_map script." \
          + " Example : DAILY_SNOW_MASKS_T31TCH_20160901_20170831.tif")
    print(
        "Usage: python compute_SOD_SMOD.py DAILY_SNOW_MASKS_T31TCH_20160901_20170831.tif T31TCH_20160901_20170831 /tmp")
    print("Example: python compute_SOD_SMOD.py input_file synthesis_id output_dir")
    print("python compute_SOD_SMOD.py version to show version")
    print("python compute_SOD_SMOD.py help to show help")


def show_version():
    """
    Show LIS version.
    :return:
    """
    print("LIS Version : {}".format(version('s2snow')))


def main(argv):
    compute_SOD_SMOD(*argv[1:])


if __name__ == "__main__":
    if len(sys.argv) < 1 or len(sys.argv) > 3:
        show_help()
    else:
        if sys.argv[1] == "version":
            show_version()
        elif sys.argv[1] == "help":
            show_help()
        else:
            main(sys.argv)
