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
#include "itkNaryFunctorImageFilter.h"
#include "itkNumericTraits.h"
#include <bitset>

namespace itk
{
namespace Functor
{
/**
 * \class SnowMask
 * \brief
 */
template< typename TInput, typename TOutput >
class SnowMask
{
public:
  typedef typename NumericTraits< TInput >::AccumulateType AccumulatorType;
  SnowMask() {}
  ~SnowMask() {}
  inline TOutput operator()(const std::vector< TInput > & B) const
  {
  std::bitset<8> bits(0x0);

  for ( unsigned int i = 0; i < B.size(); i++ )
    { 
    if ( B[i]>0 )
    { 
    bits.set(i,1);
    }
  }

  return static_cast< TOutput >( bits.to_ulong() );
  }

  bool operator==(const SnowMask &) const
  {
    return true;
  }

  bool operator!=(const SnowMask &) const
  {
    return false;
  }
};
}
/** \class NarySnowMaskImageFilter
 * \brief SnowMask  functor
 *
 */
template< typename TInputImage, typename TOutputImage >
class NarySnowMaskImageFilter:
  public
  NaryFunctorImageFilter< TInputImage, TOutputImage,
                          Functor::SnowMask< typename TInputImage::PixelType,  typename TInputImage::PixelType > >
{
public:
  /** Standard class typedefs. */
  typedef NarySnowMaskImageFilter Self;
  typedef NaryFunctorImageFilter<
    TInputImage, TOutputImage,
    Functor::SnowMask< typename TInputImage::PixelType,
                   typename TInputImage::PixelType > > Superclass;

  typedef SmartPointer< Self >       Pointer;
  typedef SmartPointer< const Self > ConstPointer;

  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Runtime information support. */
  itkTypeMacro(NarySnowMaskImageFilter,
               NaryFunctorImageFilter);

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
  NarySnowMaskImageFilter() {}
  virtual ~NarySnowMaskImageFilter() {}

private:
  NarySnowMaskImageFilter(const Self &);
  void operator=(const Self &);
};
} // end namespace itk

