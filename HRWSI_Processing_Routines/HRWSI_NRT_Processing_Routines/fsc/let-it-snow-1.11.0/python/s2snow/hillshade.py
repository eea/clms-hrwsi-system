import logging
import os
from datetime import datetime, timedelta
import time
import numpy as np
from lxml import etree
from eolab.rastertools import Hillshade
import logging
import logging.config
from osgeo import gdal, osr
from s2snow.lis_constant import AZIMUTH_PATH, ZENITH_PATH
from s2snow.lis_exception import UnknownProductException
from s2snow.otb_wrappers import band_math

_logger = logging.getLogger(__name__)
"""
This scripts compute the hillshade from a DEM and a Sentinel2 Metadata file containing the sun angles.

WARNING : IT IS NOT YET IMPLEMENTED FOR LANDSAT8 AND TAKE5 DATA

This scripts take the azimuth and zenith angles and resample them to get grids of angles with the same size as the DEM.
It computes the normal vector to each cell of the DEM, according to its neighbors. 
The hillshade is the scalar product of the sun vectors and the normal vectors.
"""

def get_grid_values_from_xml(xml_path, angle="Zenith"):
    '''Receives a XML tree node and a XPath parsing string and search for children matching the string.
       Then, extract the VALUES in <values> v1 v2 v3 </values> <values> v4 v5 v6 </values> format as numpy array
       Loop through the arrays to compute the mean.
    '''

    tree = etree.parse(xml_path)

    # get col and row steps (5 km)
    node = tree.xpath(f".//Sun_Angles_Grids/{angle}/COL_STEP")[0]
    colstep = float(node.text)
    node = tree.xpath(f".//Sun_Angles_Grids/{angle}/ROW_STEP")[0]
    # assume it's a north up image
    rowstep = -1*float(node.text)

    # get EPSG code
    epsg = tree.find(".//HORIZONTAL_CS_CODE").text

    # get grid corners coordinates
    # warning: in array geometry the lower left corner is the upper left in raster geometry
    ulx = float(tree.find(".//*[@name='upperLeft']/X").text)
    uly = float(tree.find(".//*[@name='upperLeft']/Y").text)
    lrx = float(tree.find(".//*[@name='lowerRight']/X").text)
    lry = float(tree.find(".//*[@name='lowerRight']/Y").text)

    node = tree.xpath(f".//Sun_Angles_Grids/{angle}/Values_List")[0] # VALUES
    arrays_lst = []
    for values in node:
        values_arr = [float(k) for k in values.text.split(" ")]
        arrays_lst.append(values_arr)

    # We assume that the above coordinates correspond to the *centers* of corner pixels
    # otherwise the 23x23 grid would have an extra row and column somewhere
    ulxMTD = ulx - colstep/2
    ulyMTD = uly - rowstep/2

    # define the affine transformation coefficients
    geoTransform = (ulxMTD, colstep, 0, ulyMTD, 0, rowstep)

    # create spatial reference
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromEPSG(int(epsg))

    return np.array(arrays_lst), geoTransform, spatialRef


def resample_angles(angle_array, angle_geoTransform, angle_spatialRef, ref_dem, output_angle):
    """
    Resample the small grid of angles to the size of the dem to take into consideration the variation of sun angles given in the metadata files.

    :param angle_array: The angles from the metadata file given as an array
    :param ref_dem: the gdal Dataset object that will serve for the target resolution and georeferencing during the resampling
    :param output_angle: The path of the file where the resampled angles will be written.
    :return Gdal object: the gdal Dataset with the resampled angles
    """
    driver = gdal.GetDriverByName("GTiff")
    angles = driver.Create(output_angle, angle_array.shape[0], angle_array.shape[1], 1, gdal.GDT_Float32)
    angles.SetGeoTransform(angle_geoTransform)
    angles.SetProjection(angle_spatialRef.ExportToWkt())
    angles.GetRasterBand(1).WriteArray(angle_array)
    angles.FlushCache()
    
    gdal.Warp(output_angle, angles, resampleAlg=gdal.GRIORA_Cubic, width=ref_dem.RasterXSize, height=ref_dem.RasterYSize)

    return gdal.Open(output_angle)


def sun_vector_from_az_zen(zenith, azimuth):
    """
    Compute the sun vector from azimuth and zenith angles. The sun vector points towards the sun is normalized.
    """
    sz = np.cos(np.radians(zenith))
    sx = np.cos(np.radians(azimuth)-np.pi/2)
    sy = np.sin(np.radians(azimuth)-np.pi/2)
    norm_ = sx**2 + sy**2 + sz**2
    return np.array([sx/norm_, sy/norm_, sz/norm_])


def gradient(grid, length_x, length_y=None):
    """
    Calculate the numerical gradient of a matrix in X, Y and Z directions.

    :param grid: Matrix
    :param length_x: Length between two columns
    :param length_y: Length between two rows
    :return:
    """
    if length_y is None:
        length_y = length_x

    if len(grid.shape) != 2:
        msg = "In the computation of the gradient for the relief shade mask, grid should be a two dimension matrix."
        logging.error(msg)
        raise UnknownProductException(msg)


    grad = np.empty((*grid.shape, 3))
    grad[:] = np.nan
    grad[:-1, :-1, 0] = 0.5 * length_y * (
        grid[:-1, :-1] - grid[:-1, 1:] + grid[1:, :-1] - grid[1:, 1:]
    )
    grad[:-1, :-1, 1] = 0.5 * length_x * (
        grid[:-1, :-1] + grid[:-1, 1:] - grid[1:, :-1] - grid[1:, 1:]
    )
    grad[:-1, :-1, 2] = length_x * length_y

    # Copy last row and column
    grad[-1, :, :] = grad[-2, :, :]
    grad[:, -1, :] = grad[:, -2, :]

    area = np.sqrt(
        grad[:, :, 0] ** 2 +
        grad[:, :, 1] ** 2 +
        grad[:, :, 2] ** 2
    )
    for i in range(3):
        grad[:, :, i] /= area
    return grad


def save_alt(geo_array, ref_geo, name):
    """
    Function to save .tif files.

    :param geo_array: The numpy array with the values of the tif file
    :param ref_geo: The gdal Dataset object containing the georeference of our final file
    :param name: the name of the final .tif file (ex: "Angles.tif")
    :return None:
    """

    [rows, cols] = geo_array.shape
    driver = gdal.GetDriverByName("GTiff")
    outdata_water = driver.Create(name, cols, rows, 1, gdal.GDT_Float32)
    outdata_water.SetGeoTransform(ref_geo.GetGeoTransform())##sets same geotransform as input
    outdata_water.SetProjection(ref_geo.GetProjection())##sets same projection as input
    outdata_water.GetRasterBand(1).WriteArray(geo_array)
    outdata_water.FlushCache() ##saves to disk!!
    return


def compute_hillshade_mask(output_file, dem_path, hillshade_lim, xml, output_folder):
    """
    Compute the hillshade from the DEM, and apply a threshold to create a mask where there is too much shadow
    :param dem_path: The Digital Elevation Model path
    :param hillshade_lim: the threshold under which the hillshade will be masked
    :param output_file: the file where the mask will be written
    :param xml: the input directory containg the METADATA file. Should be Sentinel2 format
    :param output_folder: tmp_dir
    """
    if not os.path.exists(xml):
        raise UnknownProductException(f"Could not find the Metadata {xml} file.")

    dem = gdal.Open(dem_path)

    # len_y cannot be negative
    len_x, len_y = float(np.abs(dem.GetGeoTransform()[1])), np.abs(float(np.abs(dem.GetGeoTransform()[5])))

    if len_x == 0:
        msg = "The GeoTransform of the DEM has 0 of x-wise step !"
        logging.error(msg)
        raise UnknownProductException(msg)

    dem_array = dem.ReadAsArray()
    
    # Compute the hill gradient ( https://people.geog.ucsb.edu/~kclarke/G232/terrain/Corripio_2003.pdf )
    grad = gradient(dem_array, len_x, len_y)


    # angle covers a tile of side 23*5000m, dem covers a tile of size

    # If there are NaN in the xml azimuth and zenith data, the bicubic resizing will create a zone with nan around it 
    angle_array, angle_geoTransform, angle_spatialRef = get_grid_values_from_xml(xml, angle="Zenith")
    zenith = resample_angles(angle_array, angle_geoTransform, angle_spatialRef, dem, os.path.join(output_folder, ZENITH_PATH)).ReadAsArray()
    angle_array, angle_geoTransform, angle_spatialRef = get_grid_values_from_xml(xml, angle="Azimuth")
    azimuth = resample_angles(angle_array, angle_geoTransform, angle_spatialRef, dem, os.path.join(output_folder, AZIMUTH_PATH)).ReadAsArray()
    
    sun_vector = sun_vector_from_az_zen(zenith, azimuth)

    #Compute hill shade
    hillshade = (grad[:, :, 0] * sun_vector[0, :, :] + grad[:, :, 1] * sun_vector[1, :, :] + grad[:, :, 2] * sun_vector[2, :, :])

    # Creating mask based on threshold
    hillshade_mask = (hillshade<hillshade_lim).astype(dtype=np.int8)
    save_alt(hillshade_mask, dem, output_file)

def get_azimuth_angle_from_xml(xml_path):
    """Return the average solar azimuth angle of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    p = ".//Geometric_Informations/Mean_Value_List/Sun_Angles"
    mean_az = float(tree.xpath(p + "/AZIMUTH_ANGLE")[0].text)
    return mean_az

def get_elevation_angle_from_xml(xml_path):
    """Return the average solar elevation angle of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    p = ".//Geometric_Informations/Mean_Value_List/Sun_Angles"
    mean_ele = 90 - float(tree.xpath(p + "/ZENITH_ANGLE")[0].text)
    return mean_ele

def get_spatial_res_from_xml(xml_path):
    """Return the spatial resolution of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    p = ".//Radiometric_Informations/Spectral_Band_Informations_List/Spectral_Band_Informations"
    res = int(tree.xpath(p + "/SPATIAL_RESOLUTION")[0].text)
    return res

def get_acquisition_time_from_xml(xml_path):
    """Return the acquisition date of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    node = tree.xpath(f".//Product_Characteristics/ACQUISITION_DATE")[0]
    acq_time = datetime.strptime(node.text,'%Y-%m-%dT%H:%M:%S.%fZ')
    return acq_time

def get_longitude_from_xml(xml_path):
    """Return the central longitude of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    p = ".//Geoposition_Informations/Geopositioning/Global_Geopositioning/Point"
    center_long = float(tree.xpath(p + "[@name='center']/LON")[0].text)
    return center_long

def get_latitude_from_xml(xml_path):
    """Return the central latitude of the product from the metadata
    xml_path: path to xml file
    """
    tree = etree.parse(xml_path)
    p = ".//Geoposition_Informations/Geopositioning/Global_Geopositioning/Point"
    center_lat = float(tree.xpath(p + "[@name='center']/LAT")[0].text)
    return center_lat

def isleap(year):
    """Return True for leap years, False for non-leap years."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def local_solar_time(dt, long):
    """Return local solar time accounting for the equation of time
    dt: acquisition time in UTC (datetime.datetime)
    long: longitude (float in degree)
    """
    if isleap(dt.year):
        gamma = 2 * np.pi / 366 * (dt.timetuple().tm_yday - 1 + float(dt.hour - 12) / 24)
    else:
        gamma = 2 * np.pi / 365 * (dt.timetuple().tm_yday - 1 + float(dt.hour - 12) / 24)

    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma) \
             - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma))
    tst = dt + timedelta(hours = long / 360.0 * 24) + timedelta(minutes = eqtime)
    return tst

def compute_hillshade_mask_rastertools(output_file, dem_path, xml, output_folder, dem_resolution,
                                       rastertools_window_size=1024, rastertools_radius=None):
    """
    Compute the hillshade from the DEM, using rastertools
    :param output_file: the file where the mask will be written
    :param dem_path: The Digital Elevation Model path
    :param xml: the input directory containg the METADATA file. Should be Sentinel2 format
    :param output_folder: tmp_dir
    :param dem_resolution: spatial resolution of dem or target resolution (in meters)
    :param rastertools_window_size: Size of tiles to distribute processing, default: 1024
    :param rastertools_radius: Max dist (in pixels) arunnd a point to evaluate horizontal elevation angle, default: None
    """

    # Retrieve solar angles from xml metadata
    solar_elevation = get_elevation_angle_from_xml(xml)
    solar_azimuth = get_azimuth_angle_from_xml(xml)
    logging.info(f"solar elevation angle :{solar_elevation:.3f}; solar azimuth angle : {solar_azimuth:.3f}")
    logging.info(f"dem spatial resolution : {dem_resolution}")
    logging.info(f"windows_size is set to {rastertools_window_size}")
    if rastertools_radius: logging.info(f"radius is set to {rastertools_radius}")
        
    # create the rastertool object and run hillshade computation
    start_t = time.time()
    tool = Hillshade(solar_elevation, solar_azimuth, dem_resolution, rastertools_radius)
    tool.with_output(output_folder)
    tool.with_windows(rastertools_window_size)
    hillshade_str = tool.process_file(dem_path)
    logging.info(f"Rastertools execution successful. Result is stored at {hillshade_str[-1]}")
    # Rename result file
    if os.path.exists(hillshade_str[-1]):
        os.rename(hillshade_str[-1], output_file)
    logging.info(f"Renaming file {hillshade_str[-1]} in {output_file} has been successful.")
    # measuring time computation
    end_t = time.time()
    logging.info(f"Computation time : {(end_t - start_t):.3f}")


