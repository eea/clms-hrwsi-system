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

class LisConfigurationException(Exception):
    def __init__(self, msg):
        self.msg = msg


class UnknownProductException(Exception):
    def __init__(self, msg):
        self.msg = msg


class UnknownPlatform(Exception):
    def __init__(self, msg):
        self.msg = msg


class NoProductMatchingSynthesis(Exception):
    def __init__(self, msg):
        self.msg = msg


class NoSnowProductFound(Exception):
    def __init__(self, msg):
        self.msg = msg


class NoZipFound(Exception):
    def __init__(self, msg):
        self.msg = msg