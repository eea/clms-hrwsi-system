# LIS configuration - for experts

## let_it_snow_fsc configuration

Lis configuration file description can be found here : [fsc_config_schema.json](doc/atbd/fsc_config_schema.json)
This part describes the expert use of the fsc configuration file, in particular which value is used for each parameter which can be defined multiple times.

#### general
- multi : overwrite the lis mission configuration value, defined for each mission
- mode: overwrite the lis mission configuration value, defined for each mission

#### cloud

- all_cloud_mask: overwrite the lis mission configuration value, defined for each mission
- high_cloud_mask: overwrite the lis mission configuration value, defined for each mission
- shadow_in_mask: overwrite the lis mission configuration value, defined for each mission
- shadow_out_mask: overwrite the lis mission configuration value, defined for each mission
- resize_factor: overwrite the lis mission configuration value, defined for each mission

#### fsc

- tcd: command line value will be used first, launch configuration value will be used as second, and finally configuration value will be used at last

#### shaded_snow
- "detect_shaded_snow": Activate or de activate shaded snow detection
- "hillshade_lim": Define hillshade limitation threshold
- "shaded_snow_pass": Define shaded snow pass threshold
- "rastertools_use": Activate or de rastertools hillshade detection
- "rastertools_window_size": Define size of tiles to distribute processing
- "rastertools_radius": Max distance (in pixels) around a point to evaluate horizontal elevation angle

#### water_mask

- water_mask_path: command line value will be used first, launch configuration value will be used as second, and finally configuration value will be used at last

#### inputs

- div_mask: configuration value will be used first, read value from input product will be used at last
- div_slope_threshold: overwrite the lis mission configuration value, defined for each mission
- cloud_mask: configuration value will be used first, read value from input product will be used at last
- dem: command line value will be used first if defined, launch configuration value will be used as second, and finally configuration value will be used at last
- green_band: 
  * no_band: overwrite the lis mission configuration value, defined for each mission
  * path: configuration value will be used first, read value from input product will be used at last
- red_band:
  * no_band: overwrite the lis mission configuration value, defined for each mission
  * path: configuration value will be used first, read value from input product will be used at last
- swir_band: 
  * no_band: overwrite the lis mission configuration value, defined for each mission
  * path: configuration value will be used first, read value from input product will be used at last
    
## let_it_snow_synthesis parameters

### synthesis_launch parameters

- tile_id: The identifier of the tile corresponding to the input input_products_list products (mandatory). Overload using : "-t" or "--tile_id"
- input_products_list: The input products list, containing the paths of S2 snow products only on tile_id at same resolution and size" (mandatory). Overload using : "-i" or "--input_products_list"
- densification_products_list: The densification products list, containing the paths of L8 snow products (optional). Overload using : "-d" or "--densification_products_list"
- date_start: Start of the date range for which we want to generate the snow_annual_map (DD/MM/YYYY) (mandatory). Overload using : "-b" or "--date_start"
- date_stop: Stop of the date range for which we want to generate the snow_annual_map (DD/MM/YYYY) (mandatory). Overload using : "-e" or "--date_stop"
- date_margin: The margin outside the date range to use for better interpolation results (in days) (optional). Overload using : "-m" or "--date_margin"
- output_dir: Output directory containing LIS products (mandatory). Overload using : "-o" or "--output_dir"
- log_level:Log level : INFO, DEBUG, WARNING, ERROR (optional). Overload using : "-l" or "--log_level"
- config_file: LIS configuration file - see synthesis_config_schema.json (mandatory). Overload using : "-c" or "--config_file"
- chain_version: Hysope 2 chain version (optional). Overload using : "-V" or "--chain_version"
- product_counter: Hysope 2 product counter (optional). Overload using : "-n" or "--product_counter"

If the user choose to overload a parameter, this parameter on the file is not used but it use the parameter given as argument.

### synthesis_config parameters

- ram: Maximum number of RAM memory used by the program. (optional)
- nb_threads: Maximum number of threads use by the program. (optional)
- output_dates_filename: Path to output_dates, containing all dates you want in the output. (optional, by default step between two dates is one day)


