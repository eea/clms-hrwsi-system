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
#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "otbWrapperChoiceParameter.h"

#include "histo_utils.h"
#include "itkImageToHistogramFilter.h"

namespace otb
{
namespace Wrapper
{
class ComputeNbPixels : public Application
{
public:
  /** Standard class typedefs. */
  typedef ComputeNbPixels                Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  typedef Int16ImageType InputImageType;
  typedef itk::Statistics::ImageToHistogramFilter<InputImageType> HistogramFilterType;
  typedef HistogramFilterType::HistogramSizeType SizeType;
  typedef HistogramFilterType::HistogramType  HistogramType;
  
  /** Standard macro */
  itkNewMacro(Self)

  itkTypeMacro(ComputeNbPixels, otb::Wrapper::Application)

  private:
  void DoInit() override
  {
    SetName("ComputeNbPixels");
    SetDescription("Compute Snow line application");

    // Documentation
    SetDocLongDescription("This application does compute the ZS value and output the histogram of snow pixels per altitude slices.");
    SetDocLimitations("None");
    SetDocAuthors("Manuel Grizonnet");
    SetDocSeeAlso("TODO");
    AddDocTag(Tags::Multi);

    AddParameter(ParameterType_InputImage, "in", "Input image");
    SetParameterDescription( "in", "Input image");

    AddParameter(ParameterType_Int, "lower", "lower bound");
    SetParameterDescription("lower", "lower bound");

    AddParameter(ParameterType_Int, "upper", "upper bound");
    SetParameterDescription("upper", "upper bound");

    AddRAMParameter();

    AddParameter(ParameterType_Int, "nbpix",  "Nb pixels");
    SetParameterDescription("nbpix", "Nb pixels");
    SetParameterRole("nbpix", Role_Output);
    
    
    SetDocExampleParameterValue("in", "input.tif");
    SetDocExampleParameterValue("lower", "10");
    SetDocExampleParameterValue("upper", "100");
  }

  void DoUpdateParameters() override
  {
    // Nothing to do here : all parameters are independent
  }

  void DoExecute() override
  {
    // Read DEM image

    InputImageType * inImage = GetParameterImage<InputImageType>("in");

    // Instantiating object (compute min/max from dem image)
    histogramFilter = HistogramFilterType::New();

    histogramFilter->SetInput(inImage);

    // TODO is it really needed?
    histogramFilter->SetAutoMinimumMaximum( false );
    histogramFilter->SetMarginalScale( 10000 );

    HistogramFilterType::HistogramMeasurementVectorType lowerBound(1);
    HistogramFilterType::HistogramMeasurementVectorType upperBound(1);

    lowerBound.Fill(GetParameterInt("lower"));
    upperBound.Fill(GetParameterInt("upper"));
  
    histogramFilter->SetHistogramBinMinimum( lowerBound );
    histogramFilter->SetHistogramBinMaximum( upperBound );
    
    SizeType size(1);
    size.Fill(2); 

    histogramFilter->SetHistogramSize( size );
    histogramFilter->Update();

    const HistogramType * histogram = histogramFilter->GetOutput();

    //Compute and return number of pixels between bounds
    const int nbPix = histogram->GetFrequency(1);

    otbAppLogINFO(<<"Number of pixels computed: "<<nbPix);
    SetParameterInt("nbpix", nbPix, false);
  }

  HistogramFilterType::Pointer histogramFilter;
};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeNbPixels)

