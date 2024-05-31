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

import os, sys
import os.path as op
from lxml import etree

def main(argv):
	minsnowthreshold = argv[1]
	maxsnowthreshold = argv[2]
	mincloudthreshold = argv[3]
	maxcloudthreshold = argv[4]
	
	total_images = 0
	
	for root, dirs, files in os.walk("../python/s2snow"):
		for name in files:
			if name == "metadata.xml":
				tree = etree.parse(op.join(root, name))
				snow_percent = float(tree.find("./Global_Index_List/QUALITY_INDEX/[@name='SnowPercent']").text)
				cloud_percent = float(tree.find("./Global_Index_List/QUALITY_INDEX/[@name='CloudPercent']").text)
				
				# Find potential
				if snow_percent > minsnowthreshold and cloud_percent > mincloudthreshold and snow_percent < maxsnowthreshold and cloud_percent < maxcloudthreshold :
					print(root)
					print(("snow percent: " + str(snow_percent)))
					print(("cloud percent: " + str(cloud_percent)))
					total_images += 1
					
	print(("total images :" + str(total_images)))

if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("Missing arguments")
	else:
		main(sys.argv)
