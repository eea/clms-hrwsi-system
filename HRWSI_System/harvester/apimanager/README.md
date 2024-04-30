# API Manager

API Manager class allows to update HRWSI Database with new real input from WEkEO API or HRWSI Database API.

The principle is as follows:

- *[ApiManager](api_manager.py)* is the class that allows to write processing conditions for each different input type. These conditions are there to clarify the search for input data. In particular, the type of image wanted, the type of processing to be applied, and conditions on the measurement date and the date of publication - them being respectively in the last m and p days, m and p varying depending on the type of processing required.

- *[WekeoApiManager](wekeo_api_manager.py)* is a sub class of *[ApiManager](api_manager.py)*. Its objective is to collect required data from the WEkEO API and transform it to match the database input format. This class can use two configuration files : one with a tile list and another with a WKT geography to limit the collected rasters amount. Configuration files are optional. **Warning**, a tile list can't be used whithout a geometry. The contrary isn't true.

- *[HRWSIDatabaseApiManager](hrwsi_database_api_manager.py)* is also a sub class of *[ApiManager](api_manager.py)*. Its goal is the same as *[WekeoApiManager](wekeo_api_manager.py)* but the search is targeted to the Database products table. Indeed, if an L1C input image is processed into an L2A product, this L2A product can become an input to be processed into an L2B raster.

The output of these classes mains is a tuple of data corresponding to the HRWSI Database input table format. This tuple is then processed by Harvester to feed the database with new input rows.

The [config.yaml](config.yaml) file contains useful information to connect to the WEkEO and the HRWSI Database API.

## Database Utils

In this folder, we can find two scripts to feed the HRWSI database with artificial data : the first to create inputs and the second to create products. These two files need a configuration file to personalize the data creation.
