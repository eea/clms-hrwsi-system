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

# Build our library
add_library( histo_utils SHARED histo_utils.cxx )
target_link_libraries(histo_utils ${OTB_LIBRARIES})

# Install for executables and libraries
install(TARGETS histo_utils
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib/static)

# Create the ComputeCloudMask OTB application
otb_create_application(NAME           ComputeCloudMask
                       SOURCES        ComputeCloudMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeSnowMask OTB application
otb_create_application(NAME           ComputeSnowMask
                       SOURCES        ComputeSnowMask.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeContour OTB application
otb_create_application(NAME           ComputeContours
                       SOURCES        ComputeContours.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})

# Create the ComputeSnowLine OTB application
otb_create_application(NAME           ComputeSnowLine
                       SOURCES        ComputeSnowLine.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES} histo_utils)

# Create the ComputeNbPixels OTB application
otb_create_application(NAME           ComputeNbPixels
                       SOURCES        ComputeNbPixels.cxx
                       LINK_LIBRARIES ${OTB_LIBRARIES})
