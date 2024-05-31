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
#include "itkUnaryFunctorImageFilter.h"
#include "itkNumericTraits.h"
#include <bitset>


namespace itk
{
  namespace Functor
  {
    // Description class

    template<typename TInput, typename TOutput> class CloudMask
    {
    public:
      typedef typename NumericTraits< TInput >::AccumulateType AccumulatorType;
      CloudMask() {}
      ~CloudMask(){}

      void SetCloudMask(const unsigned int val)
      {
        m_cloud_mask_value = val;
      }

      inline TOutput operator()(const TInput& B) const
      {
        // Allocate a bitset of size 8 to handle theia cloud mask coded on 8 bits and landsat8 L2A from nasa coded on 16 bits
        std::bitset<16> bits(B);
        std::bitset<16> mask_bits(m_cloud_mask_value);
        std::bitset<16> result;
        result = bits & mask_bits;
        if(result == mask_bits)
          return static_cast<TOutput>(1);
        else
          return static_cast<TOutput>(0);
      }
      bool operator==(const CloudMask &) const
      {
        return true;
      }

      bool operator!=(const CloudMask &) const
      {
        return false;
      }
    private:
      int m_cloud_mask_value;
    };
  }
  // Description functor
  template<typename TInputImage, typename TOutputImage> class UnaryCloudMaskImageFilter:
    public
    UnaryFunctorImageFilter< TInputImage, TOutputImage,
                            Functor::CloudMask< typename TInputImage::PixelType, typename TInputImage::PixelType > >
  {
  public:
    typedef UnaryCloudMaskImageFilter Self;
    typedef UnaryFunctorImageFilter<
    TInputImage, TOutputImage,
    Functor::CloudMask< typename TInputImage::PixelType,
                   typename TInputImage::PixelType > > Superclass;

  typedef SmartPointer< Self >       Pointer;
  typedef SmartPointer< const Self > ConstPointer;

  void SetCloudMask(const unsigned int val)
  {
    this->GetFunctor().SetCloudMask(val);
  }
  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Runtime information support. */
  itkTypeMacro(UnaryCloudMaskImageFilter,
               UnaryFunctorImageFilter);

#ifdef ITK_USE_CONCEPT_CHECKING
  // Begin concept checking
  itkConceptMacro( InputConvertibleToOutputCheck,
                   ( Concept::Convertible< typename TInputImage::PixelType,
                                           typename TOutputImage::PixelType > ) );
  itkConceptMacro( InputHasZeroCheck,
                   ( Concept::HasZero< typename TInputImage::PixelType > ) );
  // End concept checking
#endif

  protected:
  UnaryCloudMaskImageFilter() {}
  virtual ~UnaryCloudMaskImageFilter() {}

  private:
  UnaryCloudMaskImageFilter(const Self &);
  void operator=(const Self &);

  };
}
