# Let-it-snow
## Synopsis

This code implements :
* snow cover extent detection algorithm LIS (Let It Snow) for Landsat-8 and SPOT4-Take5 data. 
* fractional snow cover (FSC) for Sentinel-2 (which includes snow coverage)
* temporal syntheses based on time series of snow products (snow cover and/or FSC). 

The algorithm documentation with examples is available here:

* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1414452.svg)](https://doi.org/10.5281/zenodo.1414452)

Access to Theia Snow data collection (L2B and L3B):

* [![DOI:10.24400/329360/f7q52mnk](https://zenodo.org/badge/DOI/10.24400/329360/f7q52mnk.svg)](http://doi.org/10.24400/329360/f7q52mnk)

How to cite:

*  Gascoin, S., Grizonnet, M., Bouchet, M., Salgues, G., and Hagolle, O.: Theia Snow collection: high-resolution operational snow cover maps from Sentinel-2 and Landsat-8 data, Earth Syst. Sci. Data, 11, 493–514, [https://doi.org/10.5194/essd-11-493-2019](https://doi.org/10.5194/essd-11-493-2019), 2019.


The input files are Sentinel-2 or Landsat-8 level-2A products from the [Theia Land Data Centre](https://theia.cnes.fr/) or [SPOT-4/5 Take 5 level-2A products](https://spot-take5.org) and a Digital Terrain Model (DTM). The output is a Level-2B snow product.

The syntheses are temporally aggregated (level-3A) products derived from individual snow products after gapfilling. The three products are: the snow cover duration, the snow disappearance date and the snow appearance date. These products are typically computed over a hydrological year (more details : [Snow cover duration map](doc/snow_annual_map.md)).

## Usage
### Snow cover and FSC using "let_it_snow_fsc"

The easy way to launch snow detection is :

```bash
python let_it_snow_fsc.py –j {launch_configuration_file.json}
```
with launch_configuration_file.json :

```
{
  "input_dir"           : "XXX/SENTINEL2A_20210415-105910-624_L2A_T30TYN_C_V2-2",
  "output_dir"          : "XXX/output",
  "dem"                 : "XXX/Copernicus_DSM/world.vrt",
  "tcd"                 : "XXX/TCD_30TYN.tif",
  "log"                 : "INFO",
  "water_mask"          : "XXX/eu_hydro_20m_30TYN.tif",
  "relief_shadow_mask"  : "XXX/hillshade.tif",
  "config_file"         : "XXX/lis_configuration.json",
  "chain_version"       : "1.8",
  "product_counter"     : "1"
}
```

All launch parameters are described in [fsc_launch_schema.json](doc/atbd/fsc_launch_schema.json) 
and can be **overwritten** by the following command line options: 
```
* "-i", "--input_dir"           - Path to input directory, containing L2A Theia Product or this directory as zip
* "-o", "--output_dir"          - Path to output directory; which will contains FSC Product
* "-l", "--log_level"           - Log level between ['INFO', 'DEBUG', 'WARNING', 'ERROR'] (optional)
* "-c", "--config_file"         - Path to lis configuration file
* "-d", "--dem"                 - Path to dem file
* "-t", "--tcd"                 - Path to tree cover density file (optional)
* "-w", "--water_mask"          - Path to water mask file (optional)
* "-s", "--relief_shadow_mask"  - Path to relief shadow mask (optional)
* "-V", "--chain_version"       - Chain version in the operational system (optional)
* "-n", "--product_counter"     - Product counter number (optional)
```

In the following example, input directory and output_directory are overwritten from launch_configuration file
```bash
python let_it_snow_fsc.py –j {xx/launch_configuration_file.json} -i {xx/input_dir} -o {xx/output_dir}
```

It can also be launched like this :
```bash
python let_it_snow_fsc.py –c {xx/lis_configuration.json} -i {xx/input_dir} -o {xx/output_dir} -d {xx/dem_file}
```

Be aware that:
* Tree cover density file is only used for FSC computation (only available for Sentinel-2 products). If not defined for Sentinel-2 snow detection, only FSC-TOC (top of canopy) will be computed.
* Snow detection without water mask could lead to confusions between snow and water.
* Lis configuration file contains algorithm's parameters. Default configuration is available here : [lis_default_configuration.json](doc/lis_default_configuration.json). 
As an expert, you can look at its description file [fsc_config_schema.json](doc/atbd/fsc_config_schema.json) and explaination about how to change specific parameters in [LIS configuration for experts](doc/LIS_configuration_for_experts.md). 

You can use the command line option '-v' or '--version' to know lis version.

[Algorithm Theoretical Basis Documentation](doc/atbd/ATBD_CES-Neige.tex) gives more information about the scientific roles of these parameters.

NB: To build DEM data download the SRTM files corresponding to the study area and build the .vrt using gdalbuildvrt. Edit config.json file to activate preprocessing : Set "preprocessing" to true and set the vrt path.
Warning : DEM with nodata value could alter snow detection. zs should be contained between [-431, 8850].

### Snow synthesis using "let_it_snow_synthesis"

Run the python script let_it_snow_synthesis.py with a json launch file as unique argument:
```bash
python let_it_snow_synthesis.py –j {xx/lis_synthesis_launch_file.json}
```
All launch parameters are described in [synthesis_launch_schema.json](doc/atbd/synthesis_launch_schema.json)
and can be **overwritten** by the following command line options: 
```
* "-t", "--tile_id"                     - Tile identifiant
* "-i", "--input_products_list"         - Path to inputs products, containing S2 snow products (snow coverage and/or FSC)
* "-d", "--densification_products_list" - Path to densification products, containing L8 snow products (optional)
* "-b", "--date_start"                  - Start date defining the synthesis period
* "-e", "--date_stop"                   - Stop date defining the synthesis period
* "-m", "--date_margin"                 - date margin related to start and stop date
* "-o", "--output_dir"                  - Path to output directory; which will contains synthesis product
* "-l", "--log_level"                   - Log level ('INFO', 'DEBUG', 'WARNING', 'ERROR')
* "-c", "--config_file"                 - Path to configuration file
* "-V", "--chain_version"               - Chain version in the operational system (optional)
* "-n", "--product_counter"             - Product counter number (optional)
```

In the following example, data margin overwritten from launch_configuration file.
```bash
python let_it_snow_synthesis.py –j {path_to_synthesis_launch.json} –m {value_of_date_margin}
```
Synthesis configuration file contains system's parameters. Default configuration is available here : [synthesis_default_configuration.json](doc/synthesis_default_configuration.json). 
As an expert, you can look at its description file [synthesis_config_schema.json](doc/atbd/synthesis_config_schema.json) 

Algorithm is detailled here : [Snow Annual Map](doc/snow_annual_map.md)

You can use the command line option '-v' or '--version' to know lis version.

## Products format

### Snow product

Since lis 1.7, product name matches the following nomenclature :

LIS_<*mission*><*tag*><*chain_version*>_<*product_counter*>

LIS FSC generates the following files for S2 :

- Raster: **LIS\_S2-SNOW-FSC\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, 
- Raster: **LIS\_S2-SNOW-FSC-QCFLAGS\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**

or
- Raster: **LIS\_S2-SNOW-FSC-TOC\_<*tag*>_<*chain_version*>_<*product_counter*>.tif** (if Tree cover density is not defined) 

LIS FSC generates the following files for L8 :
- Raster: **LIS\_L8-SNOW-MSK\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, 

with <**tag**> = <**tile**><**acquisition_date**>

Moreover, in the tmp directory:

* LIS_SNOW_ALL: Binary mask of snow and clouds.
  * 1st bit: Snow mask after pass1
  * 2nd bit: Snow mask after pass2
  * 3rd bit: Clouds detected at pass0
  * 4th bit: Clouds refined  at pass0
  * 5th bit: Clouds initial (all_cloud)
  * 6th bit: Slope flag (optional 1: bad slope correction)

For example if you want to get the snow from pass1 and clouds detected from pass1 you need to do:
```python
pixel_value & 00000101
```
* LIS_SEB: Raster image of the snow mask and cloud mask.
  * 0: No-snow
  * 100: Snow
  * 205: Cloud including cloud shadow
  * 255: No data
* SEB_VEC: Vector image of the snow mask and cloud mask. Two fields of information are embedded in this product. SEB (for Snow Extent Binary) and type.
  * SEB field :
     * 0: No-snow
     * 100: Snow
     * 205: Cloud including cloud shadow
     * 255: No data
* LOG file: **lis.log**, the log file for the standard and error output generated during processing
     
### Snow syntheses 

Since lis 1.7, synthesis name matches the following nomenclature :

LIS_<*mission*><*tag*><*chain_version*>_<*product_counter*>

LIS synthesis generates the following files:

- Raster: **LIS\_<*mission*>-SNOW-SCD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the snow cover duration map (SCD), pixel values within [0-number of days] corresponding the number of snow days.

- Raster: **LIS\_<*mission*>-SNOW-SMOD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the date of snow disappearance (Snow Melt-Out Date), defined as the last date of the longest snow period. The dates are given in number of days since the first day of the synthesis.

- Raster: **LIS\_<*mission*>-SNOW-SOD\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the date of snow appearance (Snow Onset Date), defined as the first date of the longest snow period. The dates are given in number of days since the first day of the synthesis.

- Raster: **LIS\_<*mission*>-SNOW-NOBS\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the number of clear observations to compute the SCD, SMOD and SOD syntheses

- Raster: **LIS\_<*mission*>-SNOW-NSP\_<*tag*>_<*chain_version*>_<*product_counter*>.tif**, the number of snow periods (NSP). A snow period is a duration with snow between two durations without snow.

with :
- <**tag**> : <**tile**><**synthesis_start_date**><**synthesis_stop_date**>
- <**mission**> : S2 or S2L8 (if densification is used)

Output directory will also contain the following files in the tmp directory :

- Text file: **input_dates.txt**, the list of observation dates in the non-interpolated time series
- Text file: **output_dates.txt**, the list of interpolated dates

- Raster: **CLOUD\_OCCURENCE\_<*tag*>.tif**, the cloud/nodata annual map image, pixel values within [0-1] corresponding the cloud or nodata occurrences in the non-interpolated time series

- Raster: **DAILY\_SNOW\_MASKS\_<*tag*>.tif**, the snow time series file interpolated on a daily basis (1 image with one band per day). Each band are coded as follows (the interpolation removing any clouds or nodata):
	- 0: No-snow
	- 1: Snow

- LOG file: **lis.log**, the log file for the standard and error output generated during processing.


## Data set example

Sequence of snow maps produced from Sentinel-2 type of observations (SPOT-5 Take 5) over the Deux Alpes and Alpe d'Huez ski resorts are available on [Zenodo](http://doi.org/10.5281/zenodo.159563).

## Motivation

Code to generate the snow cover extent product on Theia platform.

## Installation

LIS processing chain uses CMake (http://www.cmake.org) for building from source.

### Dependencies

Following a summary of the required dependencies: 

* GDAL >=3.0
* OTB >= 7.4
* Python interpreter >= 3.8.4
* Python libs >= 3.8.4
* Python packages:
  * numpy
  * lxml
  * matplotlib
  * rasterio
* Rastertools (https://gitlab.cnes.fr/eolab/processing/rastertools) branch master (since LIS-1.11, if not installed, shaded snow will not be fully detected)
Python package dependencies:
  * pyscaffold
  * geopandas
  * scipy
  * tqdm

GDAL itself depends on a number of other libraries provided by most major operating systems and also depends on the non standard GEOS and Proj libraries. GDAL- Python bindings are also required

Python package dependencies:
* sys
* subprocess
* glob
* os
* json
* gdal

Optional dependencies:

* gdal_trace_outline can be used alternatively to gdal_polygonize.py to generate the vector layer. It requires to install [dans-gdal-scripts utilities](https://github.com/gina-alaska/dans-gdal-scripts).

### Installing from the source distribution

#### General

In your build directory, use cmake to configure your build.
```bash
cmake -C config.cmake source_lis_path
```
In your config.cmake you need to set :
```bash
LIS_DATA_ROOT
```
For OTB superbuild users these cmake variables need to be set:
```bash
OTB_DIR
ITK_DIR
GDAL_INCLUDE_DIR
GDAL_LIBRARY
```
Run make in your build folder.
```bash
make
```
To install let-it-snow application and the s2snow python module.
In your build folder:
```bash
make install
```

Add appropriate executable rights
```bash
chmod -R 755 ${install_dir}
```

The files will be installed by default into /usr/local and add to the python default modules.
To override this behavior, the variable CMAKE_INSTALL_PREFIX must be configured before build step.

Update environment variables for LIS. Make sure that OTB and other dependencies directories are set in your environment variables:
```bash
export PATH=/your/install/directory/bin:/your/install/directory/app:$PATH
export LD_LIBRARY_PATH=/your/install/directory/lib:$LD_LIBRARY_PATH
export OTB_APPLICATION_PATH=/your/install/directory/lib:$OTB_APPLICATION_PATH
export PYTHONPATH=/your/install/directory/lib:/your/install/directory/lib/python3.8/site-packages:$PYTHONPATH
```
let-it-snow is now installed.

#### On TREX (CNES cluster)

Clone these repositories :
https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow
https://gitlab.cnes.fr/Theia/lis-build-script

Then go to lis-build-script and launch the local install of LIS:

```bash
sh ./build-lis-local.sh {path_to_master_repository} {OTB_version_number} {install_repository}
```

When the install is completed, the tests are launched. The X tests have to be OK.
let-it-snow is now installed.

## Tests
Tests list is available here : [LIS_tests.md](LIS_tests.md) in the test directory.

Enable tests with BUILD_TESTING cmake option. Use ctest command to run tests. Do not forget to clean your output test directory when you run a new set of tests.

Data (input and baseline) to run validation tests are available on Zenodo:

* [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8214966.svg)](https://doi.org/10.5281/zenodo.8214966)

Download LIS-Data and extract the folder. It contains all the data needed to run tests. Set Data-LIS path var in cmake configuration files.
Baseline : Baseline data folder. It contains output files of S2Snow that have been reviewed and validated.
Data-Test : Test data folder needed to run tests. It contains Landsat, Take5 and SRTM data.
Output-Test : Temporary output tests folder.
Do not modify these folders.


On TREX (CNES cluster), from lis-build-script directory:
```bash
sh ./launch-tests.sh {install_repository}
```

## Contributors

Aurore Dupuis (CNES), Simon Gascoin (CNRS/CESBIO), Manuel Grizonnet (CNES), Tristan Klempka, Germain Salgues (Magellium), Rémi Jugier (Magellium), Pierre Tysebaert (Thalès), Céline Raillé (Thalès), Michaël Erblang (Thalès), Guillaume Eynard-Bontemps (CNES) 

## License

This is software under the Apache License v2.0. See https://www.apache.org/licenses/LICENSE-2.0.txt
