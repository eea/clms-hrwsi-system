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

import sys 
import numpy as np
from analysis import cloud_removal

arr = np.array([255, 255, 255, 255, 255,
				205, 100, 205, 100, 255,
				100, 205, 100, 100, 205,
				255, 100, 100, 205, 100,
				255, 255, 255, 255, 100]).reshape(5,5)

cloud_removal.step3_internal(arr)

expected = np.array([255, 255, 255, 255, 255,
					 205, 100, 205, 100, 255,
					 100, 100, 100, 100, 205,
					 255, 100, 100, 205, 100,
					 255, 255, 255, 255, 100]).reshape(5,5)

if((arr==expected).all()):
	sys.exit(0)
else:
	sys.exit(1)
