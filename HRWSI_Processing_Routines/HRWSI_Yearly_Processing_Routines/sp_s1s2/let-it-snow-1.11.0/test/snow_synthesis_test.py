import os
import sys
import unittest

from s2snow.snow_synthesis import compute_CCD, build_multitemp_snow100, build_snow_mask_vrt, build_gapfilled_timeserie, compute_SCD, create_snow_annual_map_metadata
from s2snow.compute_SOD_SMOD import compute_SOD_SMOD
from s2snow.compute_NOBS import compute_NOBS
from s2snow.compute_NSP import compute_NSP


class MyTestCase(unittest.TestCase):

    def __init__(self, testname, data_test, unit_test, output_dir):
        super(MyTestCase, self).__init__(testname)
        self.data_test = data_test
        self.unit_test = unit_test + "synthesis_test/"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def test_compute_CCD(self):
        binary_cloud_mask_list =[os.path.join(self.unit_test,"20180101_cloud_binary.tif"),
                                 os.path.join(self.unit_test,"20180115_cloud_binary.tif"),
                                 os.path.join(self.unit_test,"20180131_cloud_binary.tif")]
        multitemp_cloud_vrt = os.path.join(self.unit_test,"multitemp_cloud_mask.vrt")
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        ccd = compute_CCD(self.output_dir, binary_cloud_mask_list, multitemp_cloud_vrt, synthesis_id, 512)
        self.assertTrue("CLOUD_OCCURENCE_" in ccd)
        self.assertTrue(self.output_dir in ccd)
        self.assertTrue(os.path.exists(ccd))

        
    def test_build_snow_mask_vrt(self):
        binary_snow_mask_list =[os.path.join(self.unit_test,"20180101_snow_binary.tif"),
                                 os.path.join(self.unit_test,"20180115_snow_binary.tif"),
                                 os.path.join(self.unit_test,"20180131_snow_binary.tif")]
        vrt = build_snow_mask_vrt(self.output_dir, binary_snow_mask_list)
        self.assertTrue("multitemp_snow_mask" in vrt)
        self.assertTrue(self.output_dir in vrt)
        self.assertTrue(os.path.exists(vrt))

    def test_build_multitemp_snow100(self):
        multitemp_snow100 = build_multitemp_snow100(self.output_dir, os.path.join(self.unit_test,"multitemp_cloud_mask.vrt"), 512)
        self.assertTrue("multitemp_snow100" in multitemp_snow100)
        self.assertTrue(self.output_dir in multitemp_snow100)
        self.assertTrue(os.path.exists(multitemp_snow100))
        
    def test_build_gapfilled_timeserie(self):
        multitemp_cloud_vrt = os.path.join(self.unit_test,"multitemp_cloud_mask.vrt")
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        multitemp_snow100 = os.path.join(self.unit_test,"multitemp_snow100.tif")
        input_dates_filename = os.path.join(self.unit_test,"input_dates.txt")
        output_dates_filename = os.path.join(self.unit_test,"output_dates.txt")
        gapfilled = build_gapfilled_timeserie(self.output_dir, multitemp_snow100, multitemp_cloud_vrt, input_dates_filename,
                              output_dates_filename, synthesis_id, 512)
        self.assertTrue("DAILY_SNOW_MASKS" in gapfilled)
        self.assertTrue(self.output_dir in gapfilled)
        self.assertTrue(os.path.exists(gapfilled))
        
    def test_compute_scd(self):
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        gapfilled_timeserie = os.path.join(self.unit_test,"DAILY_SNOW_MASKS_T31TCH_20180101_20180131.tif")
        output_dates = os.path.join(self.unit_test,"output_dates.txt")
        scd = compute_SCD(self.output_dir, output_dates, gapfilled_timeserie, synthesis_id, 512)
        self.assertTrue("SCD_T31TCH" in scd)
        self.assertTrue(self.output_dir in scd)
        self.assertTrue(os.path.exists(scd))
        
        
    def test_compute_sod_smod(self):
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        gapfilled_timeserie = os.path.join(self.unit_test,"DAILY_SNOW_MASKS_T31TCH_20180101_20180131.tif")
        compute_SOD_SMOD(gapfilled_timeserie, synthesis_id, self.output_dir)
        sod_file = os.path.join(self.output_dir, synthesis_id.format("SOD"))
        smod_file = os.path.join(self.output_dir, synthesis_id.format("SMOD"))

        self.assertTrue(os.path.exists(sod_file))
        self.assertTrue(os.path.exists(smod_file))

    def test_compute_nobs(self):
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        multitemp_cloud_vrt = os.path.join(self.unit_test,"multitemp_cloud_mask.vrt")
        compute_NOBS(multitemp_cloud_vrt, synthesis_id, self.output_dir)
        nobs_file = os.path.join(self.output_dir, synthesis_id.format("NOBS"))
        self.assertTrue(os.path.exists(nobs_file))

    def test_compute_nsp(self):
        synthesis_id="LIS_S2L8-SNOW-{}_T31TCH_20180101_20180131_1.7.0.tif"
        gapfilled_timeserie = os.path.join(self.unit_test,"DAILY_SNOW_MASKS_T31TCH_20180101_20180131.tif")
        compute_NSP(gapfilled_timeserie, synthesis_id, self.output_dir)
        nsp_file = os.path.join(self.output_dir, synthesis_id.format("NSP"))
        self.assertTrue(os.path.exists(nsp_file))

    def test_compute_metadata(self):
        metadata_file = os.path.join(output_dir, "LIS_METADATA.XML")
        product_list = [""]
        create_snow_annual_map_metadata(product_list, self.output_dir)
        self.assertTrue(os.path.exists(metadata_file))
        
        
if __name__ == '__main__':
    data_test = sys.argv[1]
    unit_test = sys.argv[2]
    output_dir = sys.argv[3]

    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(MyTestCase)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(MyTestCase(test_name, data_test, unit_test, output_dir))

    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
