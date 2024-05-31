#!/usr/bin/python3

import os, sys, argparse, datetime, xmltodict, yaml, uuid, shutil, json, traceback
import numpy as np
import validate_cloud_optimized_geotiff

def main():
    def deliver(sysargv,parameters,result):
        # Dump some info
        sysargv['parameters'] = parameters
        sysargv['return_code'] = result
        if 'output_dir' in sysargv:
            if not os.path.exists(sysargv['output_dir']):
                os.makedirs(sysargv['output_dir'])
            f = open(os.path.join(sysargv['output_dir'],'output_info.yaml'),'w')
            f.write(yaml.dump(sysargv))
            f.close()
        try:
            wics1io.log("Exiting with code ", result)
        except:
            print("Exiting with code ", result)
        return result
    
    baseDir = os.path.split(os.path.realpath(os.sys.argv[0]))[0]
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('parameters_file',help='Path to the configuration parameters file')
    sysargv = vars(parser.parse_args())
    if sysargv['parameters_file'] is None:
        print('21: Parameters file not given. Exiting.')
        return deliver(sysargv,{},21)
    print("Reading parameters from file")
    try:
        pFile = open(sysargv['parameters_file'],'r')
    except Exception as e:
        print('22: Parameters file cannot be read. Exiting.')
        print(e)
        return deliver(sysargv,{},22)
    try:
        parameters = yaml.load(pFile,Loader=yaml.Loader)
    except Exception as e:
        print('22: Parameters file is not a valid file. Exiting.')
        print(e)
        return deliver(sysargv,{},22)
    pFile.close()
    
    print("Checking parameters",level="INFO")
    required_parameters = ['product_title', 'tile_id',
                        'sigma0_file', 'category_file', 'coefficient_file', 'tempsum_file', 'windspeed_file',
                        'input_dir' ,
                        'water_file', 'radarshadow_file', 'imd_file', 'tcd_file', 'gl_file',
                        'intermediate_dir', 'output_dir', 'aux_dir', 'tmp_dir', 
                        'log_out_file','log_err_file'
                    ]
    
    for parameter in required_parameters:
        if parameter not in parameters:
            print("Missing parameters in parameters file: " + ",".join([param for param in required_parameters if param not in parameters]))
            print('22: Parameters file incomplete. Exiting.')
            return deliver(sysargv,parameters,22)
        
    for parameter in parameters:
        sysargv[parameter] = parameters[parameter]
        
    sysargv['output_dir'] = parameters['output_dir']
    sysargv['log_level'] = parameters['log_level'] if 'log_level' in parameters else 'DEBUG'
 
    import wics1io

    wics1io.log("Logging initialized",level="DEBUG")
    wics1io.log("HRWSI WICS1 Processor started. Parameters file was read and complete.",level="INFO")
    wics1io.log("Parameters: ",level="DEBUG")
    for parameter in parameters:
      wics1io.log("\t%s : %s" % (parameter,parameters[parameter]),level="DEBUG")  
    wics1io.log("Processor options: ",level="DEBUG")
    for parameter in sysargv:
      wics1io.log("\t%s : %s" % (parameter,sysargv[parameter]),level="DEBUG") 

    if parameters['sigma0_file'] is None or parameters['sigma0_file'] == "":
        wics1io.log('23: No input products to process.',level="ERROR")
        return deliver(sysargv,parameters,23)

    missions = 'S1'
    processingBaseline = 'V100'
    sysargv['product_title'] = sysargv['product_title'].replace('processingBaseline',processingBaseline)
    sysargv['product_title'] = sysargv['product_title'].replace('missions',missions)
    wics1io.log("Final product title is ", sysargv['product_title'],level="INFO")

    # WIC and QC
    NOICE = 1
    ICE = 100
    RADARSHADOW = 200
    NODATA = 255
    # S1 SIGMA
    NODATASIGMA = 0
    # RADARSHADOW MASK
    RADARSHADOWINLAYER = 200
    # WATER LAYER
    DRY = 0
    PERMANENTWATER = 1
    TEMPORARYWATER = 2
    TEMPORARYWATERBIT = 0
    SEAWATER = 253
    UNCLASSIFIABLE = 254
    OUTSIDEAREA = 255
    # CATEGORY
    WBTYPEDIGIT = 6 # Rightest is 1
    UNCATEGORIZED = [0,3,4]   # uncategorized, extended category
    LAKE = 1
    BADWBTYPEBIT = 1 # standing_or_uncategorized
    # TEMPERATURE
    TEMPTH = 10*5
    TEMPBIT = 2
    SUMMERBIT = 3
    # IMPERVIOUSNESS
    IMDTHH = 100
    IMDTHL = 75
    IMDBIT = 4
    # TCD
    TCDTHH = 100
    TCDTHL = 75
    TCDBIT = 5 
    # GRASSLAND
    GRASS = 1
    GRASSBIT = 6
    # WINDSPEED
    WINDTH = 5
    WINDBIT = 7
    WINDYBIT = 8

    sigma0Min, sigma0Max = (-np.inf,np.inf)
    sigma0Classes = []
    wcdMin, wcdMax = (0,366)
    wcdClasses = [NODATA]    #order important, former preferred when same count
    sigma0Res = 10
    wicRes = 60
    sigma0Shape = (10980,10980)
    wicColorMap = {
        NOICE: (0,0,255,255),
        ICE: (0,232,255,255),
        RADARSHADOW: (40,40,40,255),
        NODATA: (0, 0, 0, 0)
    }
    qcColorMap = {
        0: (93,164,0,255),
        1: (189,189,91,255),
        2: (255,194,87,255),
        3: (255,70,37,255),
        RADARSHADOW: (40,40,40,255),
        NODATA: (0, 0, 0, 0)
    }
 
    result = 0

    scale = wicRes/sigma0Res
    wicShape = tuple(map(int,(sigma0Shape[0]/scale,sigma0Shape[1]/scale)))
    if int(scale) != scale or int(sigma0Shape[0]/scale) != sigma0Shape[0]/scale or int(sigma0Shape[1]/scale) != sigma0Shape[1]/scale:
        wics1io.log("Resolutions not compliant. Bad results are expected.",level="WARNING")
    scale = int(scale)

    productDir = os.path.join(sysargv['output_dir'],sysargv['product_title'])

    productTmpDir = os.path.join(sysargv['tmp_dir'],str(uuid.uuid4()))
    os.makedirs(productTmpDir)
   
    ### WIC
    # Create empty wic
    wic = NODATA*np.ones(shape=wicShape,dtype=np.uint8)

    # Read S1
    try:
        (sigma_vh, sigma_vv), geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['sigma0_file']))
    except Exception as e:
        wics1io.log("41: Sigma0 product cannot be read.",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)
    # Resample S1 to 60m
    # Provided by Markus, varilables updated, update later to wicsio.upscale
    try:
        wics1io.log("Resampling Sigma0 product",level="DEBUG")
        reShape = [wicShape[0], 6, wicShape[1], 6]
        min1 = sigma_vh.reshape(reShape).min(-1).min(1)
        min2 = sigma_vv.reshape(reShape).min(-1).min(1)
        mask = (min1 > NODATASIGMA) & (min2 > NODATASIGMA)
        sigma_vh = sigma_vh.reshape(reShape).mean(-1).mean(1) * mask
        sigma_vv = sigma_vv.reshape(reShape).mean(-1).mean(1) * mask
        sigma_nodata = np.isinf(sigma_vh) + np.isinf(sigma_vv)
        # Convert S1 to dB
        sigma_vh = 10*np.log10(sigma_vh)
        sigma_vv = 10*np.log10(sigma_vv)
    except Exception as e:
        wics1io.log("41: Problem in resampling Sigma0 product.",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    # Set product projection
    wicGeoTransform, wicProjectionRef = (geoTransform[0],geoTransform[1]*6,geoTransform[2],geoTransform[3],geoTransform[4],geoTransform[5]*6), projectionRef

    # Read water layer
    try:
        wics1io.log("Reading water layer",level="DEBUG")
        water, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['aux_dir'],sysargv['water_file']))
    except Exception as e:
        wics1io.log("41: Problem in reading water layer.",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    # Read radarshadow mask
    try:
        wics1io.log("Reading radar shadow mask",level="DEBUG")
        radarshadow, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['radarshadow_file']))
    except Exception as e:
        wics1io.log("41: Problem in radar shadow mask.",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    # Read meteorological data
    try:
        tempsum, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['tempsum_file']))
        tempdata = True
    except:
        wics1io.log("Temperature data cannot be read: %s" % os.path.join(sysargv['input_dir'],sysargv['tempsum_file']),level="WARNING")
        tempdata = False
    try:
        # fetch values for the product raster
        tempsum = tempsum[wics1io.getMeteodataIndicesForTile(wicShape,wicGeoTransform,wicProjectionRef,tempsum.shape,geoTransform,projectionRef)]
        tempdata = True
    except:
        wics1io.log("Temperature data cannot be reprojected",level="ERROR")
        tempdata = False
    if not tempdata:
        wics1io.log("Not using temperature data",level="WARNING")
        tempsum = np.empty(shape=wicShape)
        tempsum[:] = np.nan
    try:
        windspeed, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['windspeed_file']))
        winddata = True
    except:
        wics1io.log("Wind speed data cannot be read: %s" % os.path.join(sysargv['input_dir'],sysargv['windspeed_file']),level="WARNING")
        winddata = False
    try:
        # fetch values for the product raster
        windspeed = windspeed[wics1io.getMeteodataIndicesForTile(wicShape,wicGeoTransform,wicProjectionRef,windspeed.shape,geoTransform,projectionRef)]
        winddata = True
    except:
        wics1io.log("Wind speed data cannot be reprojected",level="ERROR")
        winddata = False
    if not winddata:
        wics1io.log("Not using wind speed data",level="WARNING")
        windspeed = np.empty(shape=wicShape)
        windspeed[:] = np.nan

    try:
        # Read classification coefficients
        (beta0, beta_vv, beta_vh, beta_th, beta_th_vv, beta_th_vh), geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['coefficient_file']))
        # Classify s1 where water
            # regression / th if
        if np.sum(np.isnan(beta0)) == np.prod(beta0.shape):
            # no regression
            ice = (sigma_vv >= beta_th_vv) * (sigma_vh <= beta_th_vh) * ((water == TEMPORARYWATER) + (water == PERMANENTWATER))
        else:
            #regression
            ice = (beta0 + beta_vv * sigma_vv + beta_vh * sigma_vh < beta_th) * ((water == TEMPORARYWATER) + (water == PERMANENTWATER))
        no_ice = ~ice * ((water == TEMPORARYWATER) + (water == PERMANENTWATER))
        radarshadow = (radarshadow == RADARSHADOWINLAYER) * ((water == TEMPORARYWATER) + (water == PERMANENTWATER))

        # Mark WIC
        np.place(wic, ice, ICE)
        np.place(wic, no_ice, NOICE)
        np.place(wic, radarshadow, RADARSHADOW)
        np.place(wic, sigma_nodata, NODATA)
        np.place(wic, (tempsum >= TEMPTH)*~np.isnan(tempsum), NOICE) # TBD
        np.place(wic, (water == DRY) + (water == UNCLASSIFIABLE), NODATA)
        np.place(wic, (water == SEAWATER) + (water == OUTSIDEAREA), NODATA)

        ### QF
        # Create empty QF
        qf = np.zeros(shape=wicShape,dtype=np.uint16)

        # mark qf for temporary water
        qf = wics1io.setBit(qf, TEMPORARYWATERBIT, 1, where = water == TEMPORARYWATER)

        # mark qf for standing or unclassified water (waterbody type in category)
        category, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['input_dir'],sysargv['category_file']))
        for wbtype in [LAKE] + UNCATEGORIZED:
            qf = wics1io.setBit(qf, BADWBTYPEBIT, 1, where = ((category/(10**(WBTYPEDIGIT-1))).astype(category.dtype) % 10 == wbtype ))

        # mark qf for temperature
        qf = wics1io.setBit(qf, TEMPBIT, 1, where = ~np.isnan(tempsum))
        qf = wics1io.setBit(qf, SUMMERBIT, 1, where = (tempsum >= TEMPTH)*~np.isnan(tempsum))

        # read imperviousness
        # mark wic for urban
        imperviousness, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['aux_dir'],sysargv['imd_file']))
        qf = wics1io.setBit(qf, IMDBIT, 1, where = (imperviousness >= IMDTHL) * (imperviousness <= IMDTHH))

        # Read tcd
        # Mark qf for forest
        tcd, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['aux_dir'],sysargv['tcd_file']))
        qf = wics1io.setBit(qf, TCDBIT, 1, where = (tcd >= TCDTHL) * (tcd <= TCDTHH))

        # read grassland
        # Mark gf for grass
        grassland, geoTransform, projectionRef = wics1io.readRasters(os.path.join(sysargv['aux_dir'],sysargv['gl_file']))
        qf = wics1io.setBit(qf, GRASSBIT, 1, where = grassland == GRASS)

        # Mark qf for windspeed
        qf = wics1io.setBit(qf, WINDBIT, 1, where = ~np.isnan(windspeed))
        qf = wics1io.setBit(qf, WINDYBIT, 1, where = (windspeed >= WINDTH)*~np.isnan(windspeed))

        # Unmark qf for non water areas
        np.place(qf, (wic != ICE) * (wic != NOICE) , 0)

        ### QC
        # Create empty QC, start from good quality
        qc = np.zeros(shape=wicShape,dtype=np.uint8)

        # FLAGS: SUMMER (No ice), WINDY, LAKE, TEMPWATER, IMP, GRASS, FOREST
        # Decrease quality
        qc += wics1io.getBit(qf,BADWBTYPEBIT).astype(np.uint8)
        qc += wics1io.getBit(qf,TEMPORARYWATERBIT).astype(np.uint8)
        qc += wics1io.getBit(qf,GRASSBIT).astype(np.uint8)
        # GRASS, FOREST and IMP only overlaps extremely rarely, possibly resampling error, consider if occured
        qc += (wics1io.getBit(qf,TCDBIT)*(qc <= 3)).astype(np.uint8)
        
        # buildings on top, no good signal
        np.place(qc, wics1io.getBit(qf,IMDBIT), 3)
        # windy, no good signal
        np.place(qc, wics1io.getBit(qf,WINDYBIT) , 3) # TBD
        # radarshadow
        np.place(qc, wic == RADARSHADOW , RADARSHADOW)
        # but nothing matters if summer
        np.place(qc, wics1io.getBit(qf,SUMMERBIT) , 0) # TBD

        # masked areas
        np.place(qc, wic == NODATA, NODATA)
    except Exception as e:
        wics1io.log("41: Problem in processing ",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        return deliver(sysargv,parameters,41)

    ### Stats calculation
    # TODO

    wics1io.log("Writing rasters",level="INFO")
    try:
        wics1io.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_WIC.tif'),wic,wicGeoTransform,wicProjectionRef,wicColorMap)
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_WIC.tif'),'-q'])
        if cogCheck == 1:
            wics1io.log("61: COG validation failed for WIC.tif",level="ERROR")
            return deliver(sysargv,parameters,61)
        resourceSize = os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_WIC.tif'))
        wics1io.writeThumbnail(os.path.join(productTmpDir,'thumbnail.png'),wic,wicColorMap)

        wics1io.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'),qc,wicGeoTransform,wicProjectionRef,qcColorMap)
        resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'))
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_QC.tif'),'-q'])
        if cogCheck == 1:
            wics1io.log("61: COG validation failed for QC.tif",level="ERROR")
            return deliver(sysargv,parameters,61)
        
        wics1io.writeRaster(os.path.join(productTmpDir,sysargv['product_title'] + '_QCFLAGS.tif'),qf,wicGeoTransform,wicProjectionRef)
        resourceSize += os.path.getsize(os.path.join(productTmpDir,sysargv['product_title'] + '_QCFLAGS.tif'))
        cogCheck = validate_cloud_optimized_geotiff.main(['',os.path.join(productTmpDir,sysargv['product_title'] + '_QCFLAGS.tif'),'-q'])
        if cogCheck == 1:
            wics1io.log("61: COG validation failed for QCFLAGS.tif",level="ERROR")
            return deliver(sysargv,parameters,61)
    except Exception as e:
        wics1io.log("81: Problem in writing rasters",level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        if os.path.exists(productTmpDir):
            shutil.rmtree(productTmpDir)
        return deliver(sysargv,parameters,81)


    ### Publication json
    productionTime = datetime.datetime.utcnow()
    # SIG0_20161201T064635_20161201T064700_005717_T29UMU_10m_S1BIWGRDH_ENVEO.tif
    productStartDate = datetime.datetime.strptime(sysargv['sigma0_file'].split('_')[1],"%Y%m%dT%H%M%S")
    productEndDate = datetime.datetime.strptime(sysargv['sigma0_file'].split('_')[2],"%Y%m%dT%H%M%S")
    geometry = wics1io.getAlphashape(wic, NODATA, wicGeoTransform, wicProjectionRef)
    wics1io.log("Writing JSON Metadata",level="INFO")
    product = {
        # "collection_name": "HR-WS&I",
        "resto": {
            # "type": "Feature",
            "geometry": {
                "wkt": geometry
            },
            "properties": {
                # "productIdentifier": "/HRWSI/CLMS/Pan-European/High_Resolution_Layers/Ice/WICS1/"+productStartDate.strftime("%Y/%m/%d/")+sysargv['product_title'],
                # "title": sysargv['product_title'],
                "resourceSize": str(resourceSize), ##Byte
                # "organisationName": "EEA",
                "startDate": productStartDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##sensing start
                "endDate": productEndDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##sensing end
                "completionDate": productionTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), ##generation date of the product
                # "published": None,
                # "productType": "WICS1",
                # "mission": "S1",
                "resolution": wicRes, ##meters
                # "cloudCover": '0', #%
                # "processingBaseline": processingBaseline,
                # "host_base": "cf2.cloudferro.com:8080",
                # "s3_bucket": "HRWSI",
                # "thumbnail": "Preview/CLMS/Pan-European/High_Resolution_Layers/Snow/GFSC/"+productStartDate.strftime("%Y/%m/%d/")+sysargv['product_title']+"/thumbnail.png"
            }
        }
    }
    jsonFile = open(os.path.join(productTmpDir,'dias_catalog_submit.json'), 'w')
    json.dump(product, jsonFile)
    jsonFile.close()

    wics1io.log("Writing XML Metadata",level="INFO")
    geometryBounds = wics1io.getGeoBounds(wic,wicGeoTransform,wicProjectionRef)
    productXml = xmltodict.parse(open(os.path.join(baseDir,'WICS1_Metadata.xml'),'r').read())
    productXml['gmd:MD_Metadata']['gmd:fileIdentifier']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:contact']['gmd:CI_ResponsibleParty']['gmd:contactInfo']['gmd:CI_Contact']['gmd:address']['gmd:CI_Address']['gmd:electronicMailAddress']['gco:CharacterString'] = 'copernicus@eea.europa.eu'
    productXml['gmd:MD_Metadata']['gmd:dateStamp']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:alternateTitle']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:date']['gmd:CI_Date']['gmd:date']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:edition']['gco:CharacterString'] = processingBaseline
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:editionDate']['gco:DateTime'] = productionTime.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:identifier']['gmd:RS_Identifier']['gmd:code']['gco:CharacterString'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:citation']['gmd:CI_Citation']['gmd:otherCitationDetails']['gco:CharacterString'] = 'https://land.copernicus.eu/user-corner/technical-library'
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:pointOfContact']['gmd:CI_ResponsibleParty']['gmd:contactInfo']['gmd:CI_Contact']['gmd:address']['gmd:CI_Address']['gmd:electronicMailAddress']['gco:CharacterString'] = 'copernicus@eea.europa.eu'
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:westBoundLongitude']['gco:Decimal'] = str(geometryBounds[0])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:eastBoundLongitude']['gco:Decimal'] = str(geometryBounds[1])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:southBoundLatitude']['gco:Decimal'] = str(geometryBounds[2])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:geographicElement']['gmd:EX_GeographicBoundingBox']['gmd:northBoundLatitude']['gco:Decimal'] = str(geometryBounds[3])
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['@gml:id'] = sysargv['product_title']
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:beginPosition'] = productStartDate.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:identificationInfo']['gmd:MD_DataIdentification']['gmd:extent']['gmd:EX_Extent']['gmd:temporalElement']['gmd:EX_TemporalExtent']['gmd:extent']['gml:TimePeriod']['gml:endPosition'] = productEndDate.strftime("%Y-%m-%dT%H:%M:%S.%f")
    productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:title']['gco:CharacterString'] = productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:title']['gco:CharacterString'].replace('[VALIDATION_REPORT_FILENAME]','hrwsi-ice-qar') #update when report is ready
    productXml['gmd:MD_Metadata']['gmd:dataQualityInfo']['gmd:DQ_DataQuality']['gmd:report'][0]['gmd:DQ_NonQuantitativeAttributeAccuracy']['gmd:result']['gmd:DQ_ConformanceResult']['gmd:specification']['gmd:CI_Citation']['gmd:date']['gmd:CI_Date']['gmd:date']['gco:Date'] = '1900-01-01' #update when report is ready
    productXml['gmd:MD_Metadata']['gmd:series']['gmd:DS_OtherAggregate']['gmd:seriesMetadata'] = []

    meteoProductXml = xmltodict.parse(open(os.path.join(baseDir,'ERA5_Land_Hourly_Reanalysis_MTD.xml'),'r').read())
    productXml['gmd:MD_Metadata']['gmd:series']['gmd:DS_OtherAggregate']['gmd:seriesMetadata'].append(meteoProductXml)
    
    productXml = xmltodict.unparse(productXml, pretty=True)
    xmlFile = open(os.path.join(productTmpDir,sysargv['product_title']+'_MTD.xml'), 'w')
    xmlFile.write(productXml)
    xmlFile.close()

    try:
        shutil.copytree(productTmpDir,productDir)
    except Exception as e:
        wics1io.log("82: Problem in copying product, %s to %s" % productTmpDir, productDir,level="ERROR")
        wics1io.log(traceback.format_exc(),level='ERROR')
        # Leave the files so there can be investigations
        # if os.path.exists(productTmpDir):
        #     shutil.rmtree(productTmpDir)
        # if os.path.exists(productDir):
        #     shutil.rmtree(productDir)
        return deliver(sysargv,parameters,82)

    if os.path.exists(productTmpDir):
        shutil.rmtree(productTmpDir)

    return deliver(sysargv,parameters,result)

if __name__ == "__main__":
    sys.exit(main())
