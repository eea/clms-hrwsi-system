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

file(INSTALL ${CMAKE_CURRENT_SOURCE_DIR}/let_it_snow_fsc.py DESTINATION ${CMAKE_BINARY_DIR}/app)
file(INSTALL ${CMAKE_CURRENT_SOURCE_DIR}/let_it_snow_synthesis.py DESTINATION ${CMAKE_BINARY_DIR}/app)

install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/let_it_snow_fsc.py DESTINATION ${CMAKE_INSTALL_PREFIX}/app)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/let_it_snow_synthesis.py DESTINATION ${CMAKE_INSTALL_PREFIX}/app)
