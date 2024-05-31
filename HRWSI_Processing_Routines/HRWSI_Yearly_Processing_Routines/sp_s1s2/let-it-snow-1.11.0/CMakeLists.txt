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

PROJECT(lis)

CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

# Find necessary packages

find_package(GDAL REQUIRED)


if(NOT GDAL_FOUND)
 message(FATAL_ERROR "Cannot find GDAL. Set GDAL_INCLUDE_DIR and GDAL_LIBRARY")
endif()

if (GDAL_CONFIG) 
  # extract gdal version 
  exec_program(${GDAL_CONFIG}
    ARGS --version
    OUTPUT_VARIABLE GDAL_VERSION )
  string(REGEX REPLACE "([0-9]+)\\.([0-9]+)\\.([0-9]+)" "\\1" GDAL_VERSION_MAJOR "${GDAL_VERSION}")
  string(REGEX REPLACE "([0-9]+)\\.([0-9]+)\\.([0-9]+)" "\\2" GDAL_VERSION_MINOR "${GDAL_VERSION}")
  # check for gdal version
  if (GDAL_VERSION_MAJOR LESS 2)
    message (FATAL_ERROR "GDAL version is too old (${GDAL_VERSION}). Use 2.1 or higher.")
  endif ()
endif()

#Set python home (needed on the cnes hpc)
# FIXME Is it still needed on hal?
set(PYTHON_INCLUDE_DIRS $ENV{PYTHONHOME}/include)

find_package(PythonInterp REQUIRED)

find_package( PythonLibs 3.8 REQUIRED)
include_directories( ${PYTHON_INCLUDE_DIRS} )
 
# Link to the Orfeo ToolBox
# LIS required OTB 7.4
SET(OTB_MIN_VERSION "7.4.1")

find_package(OTB ${OTB_MIN_VERSION} REQUIRED)
if(OTB_FOUND)
  include(${OTB_USE_FILE})
else(OTB_FOUND)
  message(FATAL_ERROR
          "OTB not found. Please set OTB_DIR")
endif(OTB_FOUND)


# Output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/bin CACHE INTERNAL "Single output directory for all ARCHIVE products (static libs, import libs)")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/lib CACHE INTERNAL "Single output directory for all LIBRARY products (so, modules)")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${lis_BINARY_DIR}/bin CACHE INTERNAL "Single output directory for all RUNTIME products (executables, dlls)")

# Install dirs
if(NOT lis_INSTALL_BIN_DIR)
  set(lis_INSTALL_BIN_DIR "bin")
endif(NOT lis_INSTALL_BIN_DIR)

if(NOT lis_INSTALL_LIB_DIR)
  set(lis_INSTALL_LIB_DIR "lib")
endif(NOT lis_INSTALL_LIB_DIR)

if(NOT lis_INSTALL_INCLUDE_DIR)
  set(lis_INSTALL_INCLUDE_DIR "include")
endif(NOT lis_INSTALL_INCLUDE_DIR)

set(BUILD_SHARED_LIBS ON)

include_directories(src)

add_subdirectory(src)
add_subdirectory(python)
add_subdirectory(app)
# Add Testing subdirectory
option(BUILD_TESTING  "Build testing." OFF)

if(BUILD_TESTING)
    ENABLE_TESTING()
    INCLUDE(Dart)
    add_subdirectory(test)
endif()
