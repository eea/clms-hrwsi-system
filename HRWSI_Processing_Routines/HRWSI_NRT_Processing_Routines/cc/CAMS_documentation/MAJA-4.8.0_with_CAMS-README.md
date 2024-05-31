# Generate MAJA 4.8 L2A with CAMS

## Retrieve CAMS data

"camsdownload" script from MAJA package allow to download the correct CAMS for MAJA processing. After setting up MAJA, go back to the repository were the MAJA-4.8.0 folder (most likely the root folder of the build-pkg folder where the MAJA.run executable is found). There you can run the following command:

./MAJA-4.8.0/bin/camsdownload -d date_start -f date_end -a ../CAMS -w ../CAMS_tmp -p s2

where date_start and date_end are under the yyyymmdd format.

To be able to download CAMS data the cdsapi is used. The cds api requires identification, which is done through the .cdsapirc file. This file is to be stored at $HOME on your system. To generate it create an account with ADS (Atmosphere Data Store) instead of CDS (Climate Data Store).

More documentation can be found here :
- https://confluence.ecmwf.int/display/CKB/Atmosphere+Data+Store+%28ADS%29+documentation
- https://ads.atmosphere.copernicus.eu/api-how-to

The "camsdownload" script split the time duration given in days, then iterate over days, creating three requests for each day (two times, to retrieve the forecast from 00:00 and 12:00) to retrieve the three netcdf files needed. For long duration this is slightly unefficient. You can modify the script to force it to request the whole timespan at once. The data preparation part will be faster, but the download will take as long (one netcdf file will be downloaded instead of several, but it will be several times bigger). Please note as well that with a "regular" ads account the requests are limited to 10000 elements, which corresponds roughly to 5 days of CAMS data.

To request a whole timespan:
- go to MAJA-4.8.0/lib/python/StartMaja/cams_download/download_CAMS_daily.py
- in download_files function, in dict params, change the date field with start_date/end_date (start_date and end_date yyyy-mm-dd)

If several days of CAMS data are retrieved at once, the multi-days netcdf has to be sliced into daily netcdf, as MAJA ingest only netcdf with one day of data (or one take, as there could be two dataset per day with the 00:00 and 12:00 forecast).

## Run MAJA with CAMS

MAJA can be run with CAMS the same way as without CAMS. 

The command to run MAJA is : 

./MAJA-4.8.0/bin/maja -i work/maja_input -o L2A_CAMS_output -ucs userconf/ -m MAJA_MODE

In work/maja_input, are stored :
- the GIPP files
- the DTM (generated with dtmcreation script or retrieved from CNES/production)
- the L1C (or several if MAJA_MODE = L2BACKWARD)
- the L2A (if MAJA_MODE = L2NOMINAL)
- the CAMS data (.HDR file and .DBL.DIR folder)

Two GIPP files are to be updated to allow CAMS processing :
- S2A_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF
- S2B_TEST_GIP_L2COMM_L_ALLSITES_00001_20190626_21000101.EEF

There in <Use_Cams_Data> </Use_Cams_Data> set "true" to activate the CAMS processing, set "false" to go for default aerosol processing.
