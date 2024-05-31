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

from datetime import datetime
from datetime import timedelta
from s2snow.lis_exception import LisConfigurationException
from s2snow.utils import JSONCustomEncoder


class SynthesisConfig:


    def __init__(self, data, tile_id, input_products_list, date_start, date_stop, date_margin=0,
                 densification_products_list = []):
        self.input_products_list = input_products_list
        self.date_start = datetime.strptime(date_start, "%d/%m/%Y")
        self.date_stop = datetime.strptime(date_stop, "%d/%m/%Y")
        self.date_margin = timedelta(days=date_margin)
        self.tile_id = tile_id
        self.densification_products_list = densification_products_list
        self.nb_threads = 1
        self.output_dates_filename = "output_dates.txt"
        self.ram = 4096

        self.load_config(data)
        self.check_configuration()
        self.synthesis_id = str(self.tile_id) + "_" + self.date_start.strftime("%Y%m%d") \
                            + "_" + self.date_stop.strftime("%Y%m%d")
        self.log_configuration()

    def load_config(self, data):
        logging.info("Load configuration")

        if not self.densification_products_list:
            self.densification_products_list = data.get("densification_products_list", [])

        self.nb_threads = data.get("nb_threads", 1)
        self.output_dates_filename = data.get("output_dates_filename", "output_dates.txt")
        self.ram = data.get("ram", 4096)

    def check_configuration(self):
        if self.input_products_list is None or not self.input_products_list:
            msg = "Input products are not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

        if self.date_start is None:
            msg = "Start date is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

        if self.date_stop is None:
            msg = "Stop date is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

        if self.tile_id is None:
            msg = "Tile id is not defined."
            logging.error(msg)
            raise LisConfigurationException(msg)

    def log_configuration(self):
        logging.debug("==== Configuration ====")
        for input_product in self.input_products_list:
            logging.debug("input product : " + str(input_product))
        logging.debug("date_start : " + str(self.date_start))
        logging.debug("date_stop : " + str(self.date_stop))
        logging.debug("date_margin : " + str(self.date_margin))
        for densification_products_list in self.densification_products_list:
            logging.debug("densification_products_list : " + str(densification_products_list))
        logging.debug("output_dates_filename : " + str(self.output_dates_filename))
        logging.debug("nb_threads : " + str(self.nb_threads))
        logging.debug("ram : " + str(self.ram))

    def dump_configuration(self, dump_path, config_file, log_level, chain_version, product_counter):
        # Get the fields as a dictionary
        conf_keys = ["tile_id", "input_products_list", "date_start", "date_stop", "date_margin",
                     "densification_products_list"]
        full_data = vars(self)
        data = {key: full_data[key] for key in conf_keys}
        data["output_dir"] = dump_path
        data["config_file"] = config_file
        data["log_level"] = log_level
        data["chain_version"] = chain_version
        data["product_counter"] = product_counter
        file_path = os.path.join(dump_path, 'synthesis_config.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=JSONCustomEncoder, ensure_ascii=False, indent=4)
