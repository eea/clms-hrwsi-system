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
#include "otbImageFileWriter.h"
#include "itkImageRandomNonRepeatingIteratorWithIndex.h"
#include <iostream>

typedef itk::VectorImage< short, 2> ImageType;
const unsigned int MeasurementVectorSize = 1; // 3D vectors

void CreateImage(ImageType::Pointer image, const int nbSamples, const int pixValue);

int main(int argc, char * argv [])
{
  const int expected = atoi(argv[2]);

  const int pixValue = 255;
  
  ImageType::Pointer image = ImageType::New();
  CreateImage(image, expected, pixValue);

  //Write image to temporary directory
  typedef otb::ImageFileWriter<ImageType> WriterType;
  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(argv[1]);
  writer->SetInput(image);
  writer->Update();
  
  //Then apply computation to the temporary image
  const int result = compute_nb_pixels_between_bounds(argv[1], 0, pixValue);
  
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

void CreateImage(ImageType::Pointer image, const int nbSamples, const int pixValue)
{
  const int imgSize = nbSamples*nbSamples;
  
  // Create a black image.
  itk::Size<2> size;
  size.Fill(imgSize);
  itk::Index<2> start;
  start.Fill(0);
  itk::ImageRegion<2> region(start, size);
  image->SetRegions(region);
  image->SetNumberOfComponentsPerPixel(MeasurementVectorSize);
  image->Allocate();
  
  ImageType::PixelType zeroPixel;
  zeroPixel.SetSize(MeasurementVectorSize);
  zeroPixel.Fill(0);
  
  image->FillBuffer(zeroPixel);
  
  ImageType::PixelType pixel;
  pixel.SetSize(MeasurementVectorSize);
  pixel[0]=pixValue;

  itk::ImageRandomNonRepeatingIteratorWithIndex<ImageType> imageIterator(image, image->GetLargestPossibleRegion());
  imageIterator.ReinitializeSeed(0);  	
  imageIterator.SetNumberOfSamples(nbSamples);
 
  while(!imageIterator.IsAtEnd())
    {
    imageIterator.Set(pixel);
    ++imageIterator;
    }
}
