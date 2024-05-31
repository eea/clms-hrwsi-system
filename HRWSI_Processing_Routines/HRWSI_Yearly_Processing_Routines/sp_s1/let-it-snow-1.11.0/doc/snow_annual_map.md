# Snow cover duration map

This file describes the algorithm to generate the snow cover duration map.


## Objectives:

The objective of this algorithm is to provide the snow cover duration (SCD) at 20 m spatial resolution. It was designed to compute the SCD on a yearly basis, however it can work over a longer or shorter period of time. This product relies on LIS snow products from Sentinel-2 or Landsat-8, and uses a multi-temporal approach.

The approach is evaluated with a similar product derived from MODIS products.


**General approach:**

- First a time series is created from let-it-snow (LIS) snow cover products corresponding to the desired time range (typically an annual SCD map is computed over the period 01-Sep of year N to 31-Aug of year N+1) 
- Then, every pixel of this stack is linearly interpolated in the time dimension using the [otbImageTimeSeriesGapFilling](https://gitlab.orfeo-toolbox.org/jinglada/temporalgapfilling) application to obtain a gap-filled time series on a daily basis.
- Finally, the number of snow days per pixel is computed by temporal aggregation of the daily gap-filled time series of snow cover maps. 

## Detailed approach
### Data Collection

The snow products are collected for one type of sensor only and must be at the same resolution. The request is configured according three main parameters:
- *tile\_id*, the tile id corresponding to Theia product format (ex: "T31TCH")
- *date\_start*, the target start date for the begining of the snow map time range (ex: "01/09/2017")
- *date\_stop*, the target stop date for the begining of the snow map time range (ex: "31/08/2018")

Moreover the snow products are collected by default with a margin of +/-15 days outside the requested time range to avoid any extrapolation. This margin can be set with *date\_margin* parameter.

The products corresponding to the selection criteria are stored in *input\_products\_list*.

Note: A snow season is defined from the 1st of september to the 31th of August.

### Densification

Additional heterogeneous (different sensor, resolution) snow products can be provided trought the densification options(*use_densification* and *densification\_products\_list*) to increase the time series sampling.

These additional products are resample at the same resolution and same footprint than the main snow products. For that operation, we are currently using the [otbSuperimpose](https://www.orfeo-toolbox.org/CookBook/Applications/app_Superimpose.html) application with a Nearest Neighbor interpolator. The choice of the interpolator type is constrained by the snow mask pixel coding convention:

- 0, No-Snow
- 100, Snow
- 205, Cloud
- 255, No-data

These resampled denfication snow products are append to the empty dates of the previous collection, or fused with other products as described in the following section.

### Data fusion

In the case where multiple products are available at the same date, we perform a fusion step to obtain a single snow mask.
This fusion step allows to fill some cloud/nodata from the *input\_products\_list* with data from the *densification\_products\_list*.

It is performed in [let\_it\_snow\_synthesis.py](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/python/s2snow/let_it_snow_synthesis.py) by the method *merge\_masks\_at\_same\_date()*.

    The fusion is performed according the following selection:
      if img1 != cloud/nodata use img1 data
      else if img2 != cloud/nodata use img2 data
      else if imgN != cloud/nodata use imgN data
    The order of the images in the input list is important:
      we expect to have first the main input products
      and then the densification products

The resulting snow mask follows the same pixel encoding convention than the original snow products. 

### Data conversion and time series creation

The snow products pixel coding convention being not supported by the time series interpolation application, each snow mask is converted into two different masks:

1. a binary snow mask:
	- 0, No-snow
	- 1, Snow
1. a binary cloud/nodata mask:
	- 0, valid, clear observation
	- 1, not valid, no observation due to cloud/nodata

At this point each binary mask is append into a vrt file to match the format of time series supported by the interpolation application:

        "input_dates.txt"
        "multitemp_snow_mask.vrt"
        "multitemp_cloud_mask.vrt"

Inside the two [vrt](https://www.gdal.org/gdal_vrttut.html) files, bands are indexed according the observation dates contained in "input_dates.txt".

### Time series interpolation

The time series interpolation is then performed using the the [otbImageTimeSeriesGapFilling](https://gitlab.orfeo-toolbox.org/jinglada/temporalgapfilling) application with a linear interpolator option.
The ouput interpolated time series is sampled on a daily basis between the initial *date\_start* and *date\_stop* parameters. The sampled dates are available in the text file "output\_dates.txt", and the bands are sorted in the output image accordingly.

### Results

Finally, each daily snow mask of the interpolated time series is summed into a single band using the [otbBandMath](https://www.orfeo-toolbox.org/CookBook/Applications/app_BandMath.html) aplication. The resulting snow annual map pixels are encoded with 16 bits unsigned integers between [0-365].

Here is an example of a typical snow annual map generated by the processing.

![alt text](images/snow_annual_map_ex1.png "Annual Map on T32TLQ/T32TLP for 2017/09/01 to 2018/08/31 (S2 data)")

## Validation

The approach was validated against reference data by two methods at different steps of the processing:

1. Quality of the snow mask daily interpolation, compared to actual L8 snow products:
1. Quality of the annual snow map, compared to MODIS snow annual map obtained from daily observation

### L8 comparaison
For each L8 snow products available within the time series coverage, we generate a comparaison map between the interpolated mask and the actual L8 snow mask.

![alt-text](images/L8_interpolation_comparaison.png)

The pixels are coded as follows:

- Green: No-snow L8, interp (True-Negative)
- Blue: Snow L8 and interp (True-Positive)
- Red: No-snow L8, Snow interp (False-Positive)
- Yelow: Snow L8, No-snow interp (False-Negative)

We also generate a confusion matrix to quantify the observation made from the comparaison map.

The overall quality of the interpolation is satisfying as long as the gaps between two consecutive observations is not higher than 15 days, especially when snow changes occurs at pixel level. 

Caveats:

- The quality of the interpolation is highly dependent on the sampling of the observations contributing to the time series. In concequences, missing observation related clouds or nodata may cause interpolation artefacts by increasing the time gap between two consecutives actual observations.
- The quality of the interpolation is also dependent on the quality the snow product used in the time series, any wrong snow detection will be indifferently be interpolated and will propagate the error.

### Modis comparaison

For the Modis comparaison, we compare the Modis snow annual map obtained from a gapfilled Modis time series with the Sentinel 2 snow annual map. The two annual maps are repported below:

***S2:*** ![alt-text](images/s2_annual_map.png "S2 annual map")
***Modis:*** ![alt-text](images/modis_annual_map.png "Modis annual map")

For each maps, we compute the statistics based on elevation band. A graphic comparing the population of number of snow days is available below. The results show two main differences:

- For lower elevation bands (<1500m), S2 map shows some under detection of the snow. This can be explained by the lower s2 revisit which miss short snow periods that occurs at these altitudes.
- For higher elevation bands (>2000m), S2 map shows some over detection of the snow. This can be explained by the higher s2 resolution which better detect small snow areas present on the mountain summits. This areas are then widely interpolated causing this sligth over detection.

Notes: this results are slightly outdated as they considers only years 2015-2016, for which S2 has mainly S2A products causing a revist quite twice lower than with S2B products. The 5 days revisit of S2A and S2B, should now improved this results that need to be recomputed.

***Graph comparaison:*** ![alt-text](images/graph_comparison.png "S2 vs Modis annual map")

## Running the Snow Annual Map application

The snow annual map processing can be launch as follows:

    python let_it_snow_synthesis.py -j synthesis_launch.json

Where 'synthesis_launch.json' is a configuration file containing the supported parameters according the json schema describes by [synthesis\_launch\_schema.json](https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow/blob/develop/doc/atbd/synthesis_launch_schema.json)


## Product format

Each product are identified by a tag according the following naming convention: [TILE\_ID]\_[DATE\_START]\_[DATE_STOP]

Here is a product tag example: **T31TCH\_20170901\_20180831**

Integration into Hysope-II needs that products name matches the nomenclature :

LIS_<*mission*><*tag*><*chain_version*>_<*product_counter*>


Product content description:

- JSON file: **synthesis_launch.json**, the configuration files used for the products generation
- JSON file: **synthesis_configuration.json**, the configuration files used for the program configuration

- Raster: **LIS\_<*mission*>-SNOW-NOBS\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the number of clear observations to compute the SCD, SMOD and SOD syntheses

- Raster: **LIS\_<*mission*>-SNOW-SCD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the snow cover duration map (SCD), pixel values within [0-number of days] corresponding the number of snow days.

- Raster: **LIS\_<*mission*>-SNOW-SMOD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the date of snow disappearance (Snow Melt-Out Date), defined as the last date of the longest snow period. The dates are given in number of days since the first day of the synthesis.

- Raster: **LIS\_<*mission*>-SNOW-SOD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the date of snow appearance (Snow Onset Date), defined as the first date of the longest snow period. The dates are given in number of days since the first day of the synthesis.

On the tmp repertory :

- Raster: **DAILY\_SNOW\_MASKS\_<*tag*>.tif**, the snow time series file interpolated on a daily basis (1 image with one band per day). Each band are coded as follows (the interpolation removing any clouds or nodata):
	- 0: No-snow
	- 1: Snow
- Raster: **CLOUD\_OCCURENCE\_<*tag*>.tif**, the cloud/nodata annual map image, pixel values within [0-number of observation days] corresponding the number of cloud/nodata days among the day of observation in the non-interpolated time series

- Text file: **input_dates.txt**, the list of observation dates in the non-interpolated time series
- Text file: **output_dates.txt**, the list of interpolated dates

- LOG file: **lis.log**, the log file for the standard and error output generated during processing (optional)

Note: In case of densification, the nodata value is set automatically to 0 causing some transparency of the snow map background when displayed. 

## Snow persistence maps production

The current snow annual map production covers Pyrenees and Alps for three snow seasons (2015-2016, 2016-2017, 2017-2018), using S2 and L8 snow products [distibuted by Theia](https://theia.cnes.fr/atdistrib/rocket/#/search?collection=Snow). When the snow products were not available trough the webportal, the snow products were generated from the L2A products using LIS snow detector.
A blog post shows the results over the Pyrenees and the Alps for the snow seasons 2016-2017 and 2017-2018, which highlights the comparison of the annual snow cover duration map with ski pistes.

Link to the blog post:  [http://www.cesbio.ups-tlse.fr/multitemp/?p=14620](http://www.cesbio.ups-tlse.fr/multitemp/?p=14620).

Link to the interactive map: [http://osr-cesbio.ups-tlse.fr/echangeswww/majadata/simon/snowMaps.html](http://osr-cesbio.ups-tlse.fr/echangeswww/majadata/simon/snowMaps.html).


