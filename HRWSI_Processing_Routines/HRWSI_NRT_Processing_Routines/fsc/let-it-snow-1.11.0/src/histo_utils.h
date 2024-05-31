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

#ifndef HISTO_UTILS_H
#define HISTO_UTILS_H

#include <string>
#include "itkVectorImage.h"
#include "itkImageToHistogramFilter.h"

/**
* compute_snowline: DEPRECATED ((use ComputeSnowLine instead)
*/
short compute_snowline(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const bool reverse, const int offset, const int center_offset, const char * histo_file=NULL);

short compute_snowline_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const float fclear_lim, const bool reverse, const int offset, const int center_offset,  const char* histo_file=NULL);

short get_elev_snowline_from_bin(const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType* histogram, const unsigned int i, const float fsnow_lim, const float fclear_lim, const int offset , const  int center_offset);

/**e
 * DEPRECATED (use ComputeNbPixels instead)
 * \f int compute_nb_pixels_between_bounds(const std::string & infname, const int lowerbound, const int upperbound)
 * \brief Compute number of pixels between bounds
 */
int compute_nb_pixels_between_bounds(const std::string & infname, const int lowerbound, const int upperbound);


/**
 * \fn void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file)
 * \brief Print histogram values to file (useful to validate)
 */
void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file);

#endif //HISTO_UTILS_H

