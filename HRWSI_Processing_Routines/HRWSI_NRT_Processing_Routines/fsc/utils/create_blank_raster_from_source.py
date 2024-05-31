from osgeo import gdal
gdal.DontUseExceptions()

def create_blank_raster_from_source(input_path:str,
                                    output_path:str) -> None:

    with gdal.Open(input_path) as wl_tif:
        wl_gdal_info = gdal.Info(input_path, format='json')
        band = wl_tif.GetRasterBand(1)
        zeroed_out_wl_array = 0*band.ReadAsArray()
        
        
    #open source model file, copy it and load data
    with gdal.GetDriverByName('GTiff').Create(output_path, wl_gdal_info['size'][0], wl_gdal_info['size'][1], 1, gdal.GDT_Byte) as wl_zero_tif:
        is_gcps = 'gcps' in wl_gdal_info
        if 'gcps' in wl_gdal_info:
            assert 'geoTransform' not in wl_gdal_info
            wl_zero_tif.SetGCPs([gdal.GCP(el['x'], el['y'], el['z'], el['pixel'], el['line']) for el in wl_gdal_info['gcps']['gcpList']], wl_gdal_info['gcps']['coordinateSystem']['wkt'])
        else:
            wl_zero_tif.SetGeoTransform(tuple(wl_gdal_info['geoTransform']))
        
        outband = wl_zero_tif.GetRasterBand(1)
        outband.DeleteNoDataValue()
        #write array
        outband.WriteArray(zeroed_out_wl_array)
        outband.FlushCache()

        if not is_gcps:
            wl_zero_tif.SetProjection(wl_gdal_info['coordinateSystem']['wkt'])

if __name__ == '__main__':
    
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    
    args = parser.parse_args()
    create_blank_raster_from_source(args.input, args.output)