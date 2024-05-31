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

import numpy as np
from matplotlib import pyplot as plt
from optparse import OptionParser


def load_histo(histo_path):
        with open(histo_path) as f:
  		v = np.loadtxt(f, delimiter=",", dtype='float', comments="#", skiprows=3, usecols=(0,3,4))

        fsnow_rate=v[:,1]/(v[:,1]+v[:,2])

        #print(v[:,1])
        #print(v[:,2])
        #b = np.zeros(6).reshape(2, 3)
        
        #print(fsnow_rate)
        print(fsnow_rate[0])
        print(fsnow_rate)
        print(np.shape(fsnow_rate)[0])
        plt.plot(np.arange(np.shape(fsnow_rate)[0]), fsnow_rate[:], 'ro')
        #plt.axis([0, 6, 0, 20])
        plt.show()

def print_histo(histo_path):
	with open(histo_path) as f:
  		v = np.loadtxt(f, delimiter=",", dtype='int', comments="#", skiprows=3, usecols=(0,1,3))

	#_hist = np.ravel(v)   # 'flatten' v
	#fig = plt.figure()
	#ax1 = fig.add_subplot(111)

	#n, bins, patches = ax1.hist(v_hist, bins=50, normed=1, facecolor='green')
	#plt.show()

	print(v)

	dem=v[:,0]
	width = 0.8
	#indices = np.arange(len(dem))

	plt.bar(dem, v[:,1], width=width, color="red", label="all")
	plt.bar([i+0.25*width for i in dem], v[:,2], width=0.5*width, color="blue", alpha=1. , label="snow")

	plt.xticks(dem+width/2., 
           [i for i in dem] )

	plt.legend()	
	plt.show()

def main():
    parser = OptionParser(usage="usage: %prog [options] filename",
                          version="%prog")

    parser.add_option("-f","--file", help="absolute path to histogram file", dest="histo_path", type="string")

    (opts, args) = parser.parse_args()

    if opts.histo_path is None: 
        print("A mandatory option is missing\n")
        parser.print_help()
        exit(-1)
    else:
        load_histo(opts.histo_path)

if __name__ == '__main__':
    main()
   
