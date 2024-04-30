"""Tests for create_tuple."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.apimanager.wekeo_api_manager import WekeoApiManager
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def test_create_input_tuple_wekeo_api(
    mocker,
    get_wekeo_api_data):
    '''
    Scenario :

    - Our result of request exceed one page on WEkEO API

    Expected behaviour:

    - The second page are visited and tuple are create thanks to the information of the two pages
    - The input tuples are creating in the correct form to fit Database input
    '''

    data_page_one = get_wekeo_api_data(1)
    data_page_two = get_wekeo_api_data(2)

    # Use a mocker to simulate the result of send_request function in create_tuple of WekeoApiManager
    get_result_of_request_mock = mocker.patch.object(
        WekeoApiManager,
        'send_request',
        return_value = data_page_two
    )

    expected = (('GRS_PC', '2022-05-03T10:56:21.024Z', 'T31UDQ', 20220503, '/eodata/Sentinel-2/MSI/L1C/2022/05/03/S2A_MSIL1C_20220503T105621_N0400_R094_T31UDQ_20220503T130002.SAFE', 'S2'),
                ('GRS_PC', '2022-05-03T10:56:21.024Z', 'T31UCQ', 20220503, '/eodata/Sentinel-2/MSI/L1C/2022/05/03/S2A_MSIL1C_20220503T105621_N0400_R094_T31UCQ_20220503T130002.SAFE', 'S2'))
    GRS_PC = WekeoApiManager(processing_condition_name="GRS_PC", input_type="MSIL1C", max_day_since_publication_date=7, max_day_since_measurement_date=30)
    actual = GRS_PC.create_input_tuple(content=data_page_one, candidate_input_tuple=())

    assert expected == actual
    assert get_result_of_request_mock.assert_called_once

def test_create_input_tuple_hrwsi_database_api():
    '''
    Scenario :

    - Create input tuple thanks to products in HRWSI Database

    Expected behaviour:

    - The input tuple are creating in the correct form to fit Database input
    '''

    expected = (('TURB_PC', '2022-06-26 08:27:43', 'T59UMA', 20220626, '/HRWSI/T59UMA/MSIL1C/GRS_PC/2022/06/26/S2_MSIL1C_20220626T082243_T59UMA_20220626T082743.SAFE', 'S2'),)
    cursor = [{'product_path': '/HRWSI/T59UMA/MSIL1C/GRS_PC/2022/06/26/S2_MSIL1C_20220626T082243_T59UMA_20220626T082743.SAFE',
              'creation_date': '2022-06-26 08:27:43',
              'tile': 'T59UMA',
              'measurement_day': 20220626,
              'mission': 'S2',
              'input_type': 'L2A'}]

    TURB_PC = HRWSIDatabaseApiManager(processing_condition_name="TURB_PC", max_day_since_publication_date=7)
    actual = TURB_PC.create_input_tuple(cur=cursor, candidate_input_tuple=())

    assert expected == actual
