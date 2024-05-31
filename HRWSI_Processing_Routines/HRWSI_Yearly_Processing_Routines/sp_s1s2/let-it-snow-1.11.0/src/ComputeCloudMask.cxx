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

#include "itkUnaryCloudMaskImageFilter.h"
#include "otbImage.h"

namespace otb
{
namespace Wrapper
{
class ComputeCloudMask : public Application
{
public:
  /** Standard class typedefs. */
  typedef ComputeCloudMask              Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  typedef otb::Image<unsigned short, 2>  InputImageType;
  typedef otb::Image<unsigned char, 2>  OutputImageType;

  typedef itk::UnaryCloudMaskImageFilter<InputImageType,OutputImageType> CloudMaskFilterType;

  /** Standard macro */
  itkNewMacro(Self)

  itkTypeMacro(ComputeCloudMask, otb::Wrapper::Application)

  private:
  void DoInit() override
  {
    SetName("ComputeCloudMask");
    SetDescription("Compute Cloud Mask application");

    // Documentation
    SetDocLongDescription("This application does compute the cloud mask");
    SetDocLimitations("None");
    SetDocAuthors("Germain SALGUES");
    SetDocSeeAlso("TODO");
    AddDocTag(Tags::Multi);

    AddParameter(ParameterType_InputImage, "in", "Input image");
    SetParameterDescription( "in", "Input cloud image");

    AddParameter(ParameterType_Int, "cloudmaskvalue", "Value of the cloud mask");
    SetParameterDescription("cloudmaskvalue", "Value of the input cloud mask to extract in the output mask");
    MandatoryOn("cloudmaskvalue");

    AddRAMParameter();

    AddParameter(ParameterType_OutputImage, "out",  "Output image");
    SetParameterDescription("out", "Output cloud mask");

    SetDocExampleParameterValue("in", "input_mask.tif");
    SetDocExampleParameterValue("cloudmaskvalue", "255");
    SetDocExampleParameterValue("out", "output_mask.tif");
  }

  virtual ~ComputeCloudMask()
  {
  }

  void DoUpdateParameters() override
  {
    // Nothing to do here : all parameters are independent
  }

  void DoExecute() override
  {
    // Open list of inputs
    InputImageType::Pointer inputCloudMask = GetParameterImage<InputImageType>("in");

    m_CloudMaskFilter = CloudMaskFilterType::New();
    m_CloudMaskFilter->SetInput(0, inputCloudMask);
    m_CloudMaskFilter->SetCloudMask(GetParameterInt("cloudmaskvalue"));

    // Set the output image
    SetParameterOutputImage("out", m_CloudMaskFilter->GetOutput());
  }

  CloudMaskFilterType::Pointer m_CloudMaskFilter;

};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeCloudMask)

