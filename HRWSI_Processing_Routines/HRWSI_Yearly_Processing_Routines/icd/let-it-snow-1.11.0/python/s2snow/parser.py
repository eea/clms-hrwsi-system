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

import argparse
import os.path as op
from argparse import Action
from importlib.metadata import version


class PathAction(Action):
    """
    Manage argument as path
    """

    def __call__(self, _, namespace, values, __=None):
        abs_path = op.realpath(values)
        if not op.exists(abs_path):
            raise argparse.ArgumentTypeError("Path '{}' does not exist".format(abs_path))
        setattr(namespace, self.dest, abs_path)


def create_fsc_argument_parser():
    """
    Create argument parser

    This parser contains :
    - the input directory,
    - the output directory,
    - the log level,
    - the configuration file path,
    - the dem file path,
    - the tree cover density file path,
    - the water mask file path
    - the relief shadow mask path
    :return: argument parser
    :rtype: argparse.ArgumentParser
    """
    description = "This script is used to run the snow detector module that computes fractional snow cover" \
                  + " using OTB applications on LandSat-8/Sentinel-2 products from Theia platform"

    arg_parser = argparse.ArgumentParser(description=description,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    arg_parser.add_argument("-i", "--input_dir",
                            help="Path to input directory, containing L2A Theia Product",
                            action=PathAction, default=None)
    arg_parser.add_argument("-o", "--output_dir",
                            help="Path to output directory; which will contains FSC Product",
                            default=None)
    arg_parser.add_argument("-l", "--log_level",
                            help="Log level",
                            choices=['INFO', 'DEBUG', 'WARNING', 'ERROR'])
    arg_parser.add_argument("-c", "--config_file",
                            help="Path to configuration file",
                            action=PathAction, default=None)
    arg_parser.add_argument("-d", "--dem",
                            help="Path to dem file",
                            action=PathAction, default=None)
    arg_parser.add_argument("-t", "--tcd",
                            help="Path to tree cover density file",
                            action=PathAction, default=None)
    arg_parser.add_argument("-w", "--water_mask",
                            help="Path to water mask file",
                            action=PathAction, default=None)
    arg_parser.add_argument("-s", "--relief_shadow_mask",
                            help="Path to relief shadow mask",
                            action=PathAction, default=None)
    arg_parser.add_argument("-V", "--chain_version",
                            help="Chain version in the operational system",
                            default=None)
    arg_parser.add_argument("-n", "--product_counter",
                            help="Product counter number",
                            default=None)
    arg_parser.add_argument("-j", "--json_config_file",
                            help="Path to json config file",
                            action=PathAction, default=None)
    arg_parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(version('s2snow')))
    return arg_parser


def create_synthesis_argument_parser():
    """
    Create argument parser

    This parser contains :
    - the input-products,
    - the densification-products,
    - the start date,
    - the stop date,
    - the date margin,
    - the output directory,
    - the log level,
    - the configuration file path
    :return: argument parser
    :rtype: argparse.ArgumentParser
    """
    description = "This script is used to run the snow synthesis module that computes synthesis from FSC products"

    arg_parser = argparse.ArgumentParser(description=description,
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    arg_parser.add_argument("-t", "--tile_id",
                            help="Tile identifiant", default=None)
    arg_parser.add_argument("-i", "--input_products_list",
                            help="Path to inputs products, containing S2 FSC/snow coverage products",
                            action='append', default=None)
    arg_parser.add_argument("-d", "--densification_products_list",
                            help="Path to densification products, containing L8 snow products",
                            action='append', default=None)
    arg_parser.add_argument("-b", "--date_start",
                            help="Start date defining the synthesis period",
                            default=None)
    arg_parser.add_argument("-e", "--date_stop",
                            help="Stop date defining the synthesis period",
                            default=None)
    arg_parser.add_argument("-m", "--date_margin",
                            help="date margin related to start and stop date",
                            type=float,
                            default=15)
    arg_parser.add_argument("-o", "--output_dir",
                            help="Path to output directory; which will contains synthesis Product",
                            default=None)
    arg_parser.add_argument("-l", "--log_level",
                            help="Log level",
                            choices=['INFO', 'DEBUG', 'WARNING', 'ERROR'])
    arg_parser.add_argument("-c", "--config_file",
                            help="Path to configuration file",
                            action=PathAction, default=None)
    arg_parser.add_argument("-V", "--chain_version",
                            help="Chain version in the operational system",
                            default=None)
    arg_parser.add_argument("-n", "--product_counter",
                            help="Product counter number",
                            default=None)
    arg_parser.add_argument("-j", "--json_config_file",
                            help="Path to json config file",
                            action=PathAction, default=None)
    arg_parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(version('s2snow')))
    return arg_parser
