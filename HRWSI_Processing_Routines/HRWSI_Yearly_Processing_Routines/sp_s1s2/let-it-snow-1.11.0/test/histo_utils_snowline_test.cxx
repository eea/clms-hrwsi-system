/**
* Copyright (C) 2005-2019 Centre National d'Etudes Spatiales (CNES)
*
* This file is part of Let-it-snow (LIS)
*
*     https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include "histo_utils.h"
#include <iostream>
int main(int argc, char * argv [])
{
  const int result = compute_snowline(argv[1],argv[2],argv[3],atoi(argv[4]),atof(argv[5]),atoi(argv[6]),atoi(argv[7]),atoi(argv[8]));
 const int expected = atoi(argv[9]); 
std::cout << "result: " << result << std::endl;
if (result == expected)
  {
  return EXIT_SUCCESS;
  }
else
  {
  std::cerr << "Expected value is " << expected << " but get " << result << std::endl; 
  return EXIT_FAILURE;
  }
}
