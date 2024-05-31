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

#include "itkUnaryCloudMaskImageFilter.h"

int main(int argc, char * argv [])
{
  typedef unsigned short InputType;
  typedef unsigned char  OutputType;
  typedef itk::Functor::CloudMask<InputType, OutputType> FunctorType;
  
  FunctorType functor;

  const int inputCloudMaskValue = atoi(argv[1]);
  const int inputValue = atoi(argv[2]);
  functor.SetCloudMask(inputCloudMaskValue);

  OutputType result = static_cast<int>(functor(inputValue));
  
  if ( result != atoi(argv[3]))   
    {
      return EXIT_FAILURE;
    }
  else
    {
      return EXIT_SUCCESS;
    }
}
