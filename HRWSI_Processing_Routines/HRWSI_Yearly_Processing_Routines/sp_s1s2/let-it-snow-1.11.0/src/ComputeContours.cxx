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
#include "otbImage.h"

#include "itkBinaryContourImageFilter.h"

namespace otb
{
namespace Wrapper
{
class ComputeContours : public Application
{
public:
    /** Standard class typedefs. */
    typedef ComputeContours               Self;
    typedef Application                   Superclass;
    typedef itk::SmartPointer<Self>       Pointer;
    typedef itk::SmartPointer<const Self> ConstPointer;

    typedef otb::Image<unsigned char, 2>  InputImageType;
    typedef otb::Image<unsigned char, 2>  OutputImageType;

    // Create a Binary Contour Image Filter
    typedef itk::BinaryContourImageFilter<InputImageType,InputImageType> ContourFilterType;

    /** Standard macro */
    itkNewMacro(Self)

    itkTypeMacro(ComputeContours, otb::Wrapper::Application)

    private:
        void DoInit() override
    {
        SetName("ComputeContours");
        SetDescription("Compute Contours application");

        // Documentation
        SetDocLongDescription("This application does compute the contours of the final mask");
        SetDocLimitations("None");
        SetDocAuthors("Germain SALGUES");
        SetDocSeeAlso("TODO");
        AddDocTag(Tags::Multi);

        AddParameter(ParameterType_InputImage, "inputmask", "mask image");
        SetParameterDescription( "inputmask", "Input mask to extract contours");
        MandatoryOn("inputmask");

        AddParameter(ParameterType_Int, "foregroundvalue", "foregroundvalue");
        SetParameterDescription( "foregroundvalue", "value corresponding to the region to extract");
        MandatoryOn("foregroundvalue");

        AddParameter(ParameterType_Int, "backgroundvalue", "backgroundvalue");
        SetParameterDescription( "backgroundvalue", "value corresponding to the mask background");
        MandatoryOff("backgroundvalue");
        SetDefaultParameterInt("backgroundvalue", 0);

        AddParameter(ParameterType_Int, "fullyconnected", "cloud refine image");
        SetParameterDescription( "fullyconnected", "Input cloud refine image");

        AddRAMParameter();

        AddParameter(ParameterType_OutputImage, "out",  "Output image");
        SetParameterDescription("out", "Output contour image");
        // TODO Application can write uint8 by default
        //SetDefaultOutputPixelType("out",ImagePixelType_uint8);

        SetDocExampleParameterValue("inputmask", "input_mask.tif");
        SetDocExampleParameterValue("foregroundvalue", "255");
        SetDocExampleParameterValue("backgroundvalue", "0");
        SetDocExampleParameterValue("fullyconnected", "true");
        SetDocExampleParameterValue("out", "output_mask.tif");
    }

    virtual ~ComputeContours()
    {
    }

    void DoUpdateParameters() override
    {
        // Nothing to do here : all parameters are independent
    }

    void DoExecute() override
    {
        // Open list of inputs
        InputImageType::Pointer input_mask = GetParameterImage<InputImageType>("inputmask");

        m_ContourFilter = ContourFilterType::New();
        m_ContourFilter->SetInput(0, input_mask);
        m_ContourFilter->SetForegroundValue(GetParameterInt("foregroundvalue"));
        m_ContourFilter->SetBackgroundValue(0);
        m_ContourFilter->SetBackgroundValue(GetParameterInt("backgroundvalue"));
       
        m_ContourFilter->SetFullyConnected(GetParameterInt("fullyconnected")==1);

        // Set the output image
        SetParameterOutputImage("out", m_ContourFilter->GetOutput());
    }

    ContourFilterType::Pointer m_ContourFilter;
};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeContours)

