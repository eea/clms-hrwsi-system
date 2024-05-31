import logging

# OTB Applications
import otbApplication as otb


def band_math(il, out, exp, ram=None, out_type=otb.ImagePixelType_uint8):
    """ Create and configure the band math application
        using otb.Registry.CreateApplication("BandMath")

    Keyword arguments:
    il -- the input image list
    out -- the output image
    exp -- the math expression
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if il and out and exp:
        logging.info("Processing BandMath with args:")
        logging.info("il = " + ";".join([str(x) for x in il]))
        logging.info("out = " + out)
        logging.info("exp = " + exp)

        band_math_app = otb.Registry.CreateApplication("BandMath")
        band_math_app.SetParameterString("exp", exp)
        for image in il:
            if isinstance(image, str):
                band_math_app.AddParameterStringList("il", image)
            else:
                band_math_app.AddImageToParameterInputImageList("il", image)
        band_math_app.SetParameterString("out", out)

        if ram is not None:
            logging.info("ram = " + str(ram))
            band_math_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            band_math_app.SetParameterOutputImagePixelType("out", out_type)
        band_math_app.ExecuteAndWriteOutput()
    else:
        msg = "Parameters il, out and exp are required."
        logging.error(msg)
        raise Exception(msg)


def band_mathX(il, out, exp, ram=None, out_type=None):
    """ Create and configure the band math application
        using otb.Registry.CreateApplication("BandMathX")

    Keyword arguments:
    il -- the input image list
    out -- the output image
    exp -- the math expression
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if il and out and exp:
        logging.info("Processing BandMathX with args:")
        logging.info("il = " + ";".join([str(x) for x in il]))
        logging.info("out = " + out)
        logging.info("exp = " + exp)

        band_math_x_app = otb.Registry.CreateApplication("BandMathX")
        band_math_x_app.SetParameterString("exp", exp)
        for image in il:
            if isinstance(image, str):
                band_math_x_app.AddParameterStringList("il", image)
            else:
                band_math_x_app.AddImageToParameterInputImageList("il", image)
        band_math_x_app.SetParameterString("out", out)

        if ram is not None:
            logging.info("ram = " + str(ram))
            band_math_x_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            band_math_x_app.SetParameterOutputImagePixelType("out", out_type)
        return band_math_x_app
    else:
        msg = "Parameters il, out and exp are required."
        logging.error(msg)
        raise Exception(msg)


def super_impose(img_in, mask_in, img_out, interpolator=None,
                 fill_value=None, ram=None, out_type=None):
    """ Create and configure the otbSuperImpose application
        using otb.Registry.CreateApplication("Superimpose")

    Keyword arguments:
    img_in -- the reference image in
    mask_in -- the input mask to superimpose on img_in
    img_out -- the output image
    fill_value -- the fill value for area outside the reprojected image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and mask_in and img_out:
        logging.info("Processing otbSuperImpose with args:")
        logging.info("img_in = " + img_in)
        logging.info("mask_in = " + mask_in)
        logging.info("img_out = " + img_out)
        logging.info("interpolator = " + interpolator)

        super_impose_app = otb.Registry.CreateApplication("Superimpose")
        super_impose_app.SetParameterString("inr", img_in)
        super_impose_app.SetParameterString("inm", mask_in)
        super_impose_app.SetParameterString("out", img_out)
        super_impose_app.SetParameterString("interpolator", interpolator)

        if fill_value is not None:
            logging.info("fill_value = " + str(fill_value))
            super_impose_app.SetParameterFloat("fv", fill_value)
        if ram is not None:
            logging.info("ram = " + str(ram))
            super_impose_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            super_impose_app.SetParameterOutputImagePixelType("out", out_type)
        return super_impose_app
    else:
        msg = "Parameters img_in, img_out and mask_in are required."
        logging.error(msg)
        raise Exception(msg)


def compute_cloud_mask(img_in, img_out, cloud_mask_value, ram=512, out_type=otb.ImagePixelType_uint8):
    """ Create and configure the Compute Cloud Mask application
        using otb.Registry.CreateApplication("ComputeCloudMask")

    Keyword arguments:
    img_in -- the input image
    img_out -- the output image
    cloud_mask_value -- the value corresponding to cloud
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and img_out and cloud_mask_value:
        logging.debug("Processing ComputeCloudMask with args:")
        logging.debug("in = " + img_in)
        logging.debug("out = " + img_out)
        logging.debug("cloud_mask_value = " + cloud_mask_value)

        cloudMaskApp = otb.Registry.CreateApplication("ComputeCloudMask")
        cloudMaskApp.SetParameterString("cloudmaskvalue", cloud_mask_value)
        cloudMaskApp.SetParameterString("in", img_in)
        cloudMaskApp.SetParameterString("out", img_out)

        if ram is not None:
            logging.debug("ram = " + str(ram))
            cloudMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.debug("out_type = " + str(out_type))
            cloudMaskApp.SetParameterOutputImagePixelType("out", out_type)

        cloudMaskApp.ExecuteAndWriteOutput()
    else:
        msg = "Parameters img_in, img_out and cloud_mask_value are required"
        logging.error(msg)
        raise Exception(msg)


def compute_snow_mask(pass1, pass2, cloud_pass1, cloud_refine, initial_clouds,
                      out, slope_flag=None, ram=512, out_type=None):
    """ Create and configure the Compute Cloud Snow application
        using otb.Registry.CreateApplication("ComputeSnowMask")

    Keyword arguments:
    pass1 -- the input pass1 image
    pass2 -- the input pass2 image
    cloud_pass1 -- the input cloud pass1 image
    cloud_refine -- the input cloud refine image
    initial_clouds -- the inital all cloud image
    out -- the output image
    slope_flag -- the status of the slope
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    logging.info("Processing ComputeSnowMask with args:")
    logging.info("pass1 = " + pass1)
    logging.info("pass2 = " + pass2)
    logging.info("cloud_pass1 = " + cloud_pass1)
    logging.info("cloud_refine = " + cloud_refine)
    logging.info("initial_clouds = " + initial_clouds)
    logging.info("out = " + out)

    if pass1 and pass2 and cloud_pass1 and cloud_refine and out:
        snowMaskApp = otb.Registry.CreateApplication("ComputeSnowMask")
        snowMaskApp.SetParameterString("pass1", pass1)
        snowMaskApp.SetParameterString("pass2", pass2)
        snowMaskApp.SetParameterString("cloudpass1", cloud_pass1)
        snowMaskApp.SetParameterString("cloudrefine", cloud_refine)
        snowMaskApp.SetParameterString("initialallcloud", initial_clouds)
        snowMaskApp.SetParameterString("out", out)

        if slope_flag is not None:
            logging.info("slope_flag = " + slope_flag)
            snowMaskApp.SetParameterString("slopeflag", slope_flag)
        if ram is not None:
            logging.info("ram = " + str(ram))
            snowMaskApp.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            snowMaskApp.SetParameterOutputImagePixelType("out", out_type)

        snowMaskApp.ExecuteAndWriteOutput()
    else:
        msg = "Parameters pass1, pass2, cloud_pass1, cloud_refine, initial_clouds and out are required"
        logging.error(msg)
        raise Exception(msg)


def compute_snow_line(img_dem, img_snow, img_cloud, dz, fsnowlim, fclearlim, \
                      reverse, offset, center_offset, outhist, ram=None):
    """
    Create and configure the ComputeSnowLine application using otb.Registry.CreateApplication("ComputeSnowLine")
    :param img_dem: Input DEM image
    :param img_snow: Input snow image
    :param img_cloud: Input cloud image
    :param dz: Histogram altitude bin size
    :param fsnowlim: Minimum snow fraction in an elevation band to define zs.
    :param fclearlim: Minimum clear pixel fraction in an elevation band to define zs.
    :param reverse:
    :param offset: the offset
    :param center_offset: the center offset
    :param outhist: Histogram
    :param ram: ram for otb call default 512
    :return: snow line
    """
    if img_dem and img_snow and img_cloud:
        logging.debug("Processing ComputeSnowLine with args:")
        logging.debug(img_dem)
        logging.debug(img_snow)
        logging.debug(img_cloud)
        logging.debug(dz)
        logging.debug(fsnowlim)
        logging.debug(outhist)

        snowLineApp = otb.Registry.CreateApplication("ComputeSnowLine")
        snowLineApp.SetParameterString("dem", img_dem)
        snowLineApp.SetParameterString("ins", img_snow)
        snowLineApp.SetParameterString("inc", img_cloud)
        snowLineApp.SetParameterString("outhist", outhist)

        # Scalar parameter
        snowLineApp.SetParameterInt("dz", dz)
        snowLineApp.SetParameterFloat("fsnowlim", fsnowlim)
        snowLineApp.SetParameterFloat("fclearlim", fclearlim)
        snowLineApp.SetParameterInt("offset", offset)

        if not isinstance(center_offset, int):
            if round(center_offset, 0) != center_offset:
                raise IOError("centeroffset shoud be an integer, got %s instead with value %s => error" % (
                    type(center_offset), center_offset))
            else:
                logging.warning("WARNING: centeroffset shoud be an integer, got %s instead with value %s => "
                                "converting to int" % (type(center_offset), center_offset))
            center_offset = int(center_offset)
        snowLineApp.SetParameterInt("centeroffset", center_offset)

        if reverse:
            snowLineApp.SetParameterInt("reverse", 1)
        else:
            snowLineApp.SetParameterInt("reverse", 0)

        if ram is not None:
            logging.debug("ram = " + str(ram))
            snowLineApp.SetParameterString("ram", str(ram))

        snowLineApp.ExecuteAndWriteOutput()

        return snowLineApp.GetParameterInt("zs")
    else:
        msg = "Parameters img_dem, img_snow, img_cloud and outhist are required."
        logging.error(msg)
        raise Exception(msg)


def gap_filling(img_in, mask_in, img_out, input_dates_file=None,
                output_dates_file=None, ram=None, out_type=None):
    """ Create and configure the ImageTimeSeriesGapFilling application
        using otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")

    Keyword arguments:
    img_in -- the input timeserie image
    mask_in -- the input masks
    img_out -- the output image
    ram -- the ram limitation (not mandatory)
    out_type -- the output image pixel type  (not mandatory)
    """
    if img_in and mask_in and img_out:
        logging.info("Processing ImageTimeSeriesGapFilling with args:")
        logging.info("img_in = " + img_in)
        logging.info("mask_in = " + mask_in)
        logging.info("img_out = " + img_out)

        gap_filling_app = otb.Registry.CreateApplication("ImageTimeSeriesGapFilling")
        gap_filling_app.SetParameterString("in", img_in)
        gap_filling_app.SetParameterString("mask", mask_in)
        gap_filling_app.SetParameterString("out", img_out)

        gap_filling_app.SetParameterInt("comp", 1)
        gap_filling_app.SetParameterString("it", "linear")

        if input_dates_file is not None:
            logging.info("input_dates_file = " + input_dates_file)
            gap_filling_app.SetParameterString("id", input_dates_file)
        if output_dates_file is not None:
            logging.info("output_dates_file = " + output_dates_file)
            gap_filling_app.SetParameterString("od", output_dates_file)
        if ram is not None:
            logging.info("ram = " + str(ram))
            gap_filling_app.SetParameterString("ram", str(ram))
        if out_type is not None:
            logging.info("out_type = " + str(out_type))
            gap_filling_app.SetParameterOutputImagePixelType("out", out_type)
        return gap_filling_app
    else:
        msg = "Parameters img_in, img_out and mask_in are required."
        logging.error(msg)
        raise Exception(msg)


def get_app_output(app, out_key, mode="RUNTIME"):
    """ Custom function to return the output of an OTB application
        depending on the mode, the function return either:
        - to an object correcponding to the output in memory
        - or a filename corresponding to the output written on the disk
    """
    app_output = app.GetParameterString(out_key)
    if "?" in app_output:
        app_output = app_output.split("?")[0]

    if mode == "RUNTIME":
        app.Execute()
        app_output = app.GetParameterOutputImage(out_key)
    elif mode == "DEBUG":
        app.ExecuteAndWriteOutput()
        # @TODO uneffective command, this must be done outside the function
        app = None
    else:
        msg = "Unexpected mode"
        logging.error(msg)
        raise Exception(msg)
    return app_output
