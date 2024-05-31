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

#include "itkNarySnowMaskImageFilter.h"
#include "otbImage.h"

namespace otb
{
namespace Wrapper
{
class ComputeSnowMask : public Application
{
public:
  /** Standard class typedefs. */
  typedef ComputeSnowMask               Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  typedef otb::Image<unsigned char, 2>  InputImageType;
  typedef otb::Image<unsigned char, 2>  OutputImageType;

  // Create an SnowMask Filter
  typedef itk::NarySnowMaskImageFilter<InputImageType,OutputImageType>  SnowMaskFilterType;

  /** Standard macro */
  itkNewMacro(Self)

  itkTypeMacro(ComputeSnowMask, otb::Wrapper::Application)

  private:
  void DoInit() override
  {
    SetName("ComputeSnowMask");
    SetDescription("Compute Snow Mask application");

    // Documentation
    SetDocLongDescription("This application does compute the snow mask");
    SetDocLimitations("None");
    SetDocAuthors("Germain SALGUES");
    SetDocSeeAlso("TODO");
    AddDocTag(Tags::Multi);

    AddParameter(ParameterType_InputImage, "pass1", "pass1 image");
    SetParameterDescription( "pass1", "Input pass1 image");
    MandatoryOn("pass1");

    AddParameter(ParameterType_InputImage, "pass2", "pass2 image");
    SetParameterDescription( "pass2", "Input pass2 image");
    MandatoryOn("pass2");

    AddParameter(ParameterType_InputImage, "cloudpass1", "cloud pass1 image");
    SetParameterDescription( "cloudpass1", "Input cloud pass1 image");
    MandatoryOn("cloudpass1");

    AddParameter(ParameterType_InputImage, "cloudrefine", "cloud refine image");
    SetParameterDescription( "cloudrefine", "Input cloud refine image");
    MandatoryOn("cloudrefine");

    AddParameter(ParameterType_InputImage, "slopeflag", "slope flag image");
    SetParameterDescription( "slopeflag", "Input slope flag image");
    MandatoryOff("slopeflag");

    AddParameter(ParameterType_InputImage, "initialallcloud", "initial all cloud image");
    SetParameterDescription( "initialallcloud", "Input initial all cloud image");
    MandatoryOn("initialallcloud");

    AddRAMParameter();

    AddParameter(ParameterType_OutputImage, "out",  "Output image");
    SetParameterDescription("out", "Output cloud mask");

    SetDocExampleParameterValue("pass1", "pass1.tif");
    SetDocExampleParameterValue("pass2", "pass2.tif");
    SetDocExampleParameterValue("cloudpass1", "cloud_pass1.tif");
    SetDocExampleParameterValue("cloudrefine", "cloud_refine.tif");
    SetDocExampleParameterValue("slopeflag", "slope_flag.tif");
    SetDocExampleParameterValue("initialallcloud", "all_clouds.tif");
    SetDocExampleParameterValue("out", "output_mask.tif");
  }

  virtual ~ComputeSnowMask()
  {
  }

  void DoUpdateParameters() override
  {
    // Nothing to do here : all parameters are independent
  }

  void DoExecute() override
  {
    // Open list of inputs
    InputImageType::Pointer img_pass1 = GetParameterImage<InputImageType>("pass1");
    InputImageType::Pointer img_pass2 = GetParameterImage<InputImageType>("pass2");
    InputImageType::Pointer img_cloud_pass1 = GetParameterImage<InputImageType>("cloudpass1");
    InputImageType::Pointer img_cloud_refine = GetParameterImage<InputImageType>("cloudrefine");
    InputImageType::Pointer img_all_cloud = GetParameterImage<InputImageType>("initialallcloud");

    m_SnowMaskFilter = SnowMaskFilterType::New();
    m_SnowMaskFilter->SetInput(0, img_pass1);
    m_SnowMaskFilter->SetInput(1, img_pass2);
    m_SnowMaskFilter->SetInput(2, img_cloud_pass1);
    m_SnowMaskFilter->SetInput(3, img_cloud_refine);
    m_SnowMaskFilter->SetInput(4, img_all_cloud);

    if(IsParameterEnabled("slopeflag")){
        InputImageType::Pointer img_slope_flag = GetParameterImage<InputImageType>("slopeflag");
        m_SnowMaskFilter->SetInput(5, img_slope_flag);
    }

    // Set the output image
    SetParameterOutputImage("out", m_SnowMaskFilter->GetOutput());
  }

  SnowMaskFilterType::Pointer m_SnowMaskFilter;

};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeSnowMask)

