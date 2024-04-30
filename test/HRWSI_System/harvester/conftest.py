import os
import sys
import random
import yaml
import pytest
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.apimanager.artificial_data_for_database.create_input import random_date

@pytest.fixture(scope='function')
def get_input_example():
    '''
    get_input_example Fixture function return a random input tuple example  


    :return: an input tuple
    :rtype: tuple
    '''
    def _create_random_input_example() -> tuple[tuple]:
        with open('test/HRWSI_System/harvester/config_test.yaml', 'r', encoding="utf-8") as config_file:
            file_data = yaml.safe_load(config_file)

        processing_condition_list = file_data["processing_condition_list"]
        processing_condition = processing_condition_list[random.randint(0, len(processing_condition_list)-1)]

        tile_list = file_data["tile_list"]
        tile_name = tile_list[random.randint(0, len(tile_list)-1)]

        mission = file_data["mission"]
        input_type = file_data["input_type"]
        start_date = file_data["start_date"]
        end_date = file_data["end_date"]

        creation_date = random_date(start_date=start_date, end_date=end_date, datetime_format='%Y-%m-%d %H:%M:%S')
        measurement_day = int(creation_date.strftime("%Y%m%d"))

        input_path = f"/HRWSI/{tile_name}/{input_type}/{processing_condition}/{str(measurement_day)[:4]}/{str(measurement_day)[4:6]}/{str(measurement_day)[6:8]}/{mission}_{input_type}_{creation_date.strftime('%Y%m%dT%H%M%S')}_{tile_name}_{creation_date.strftime('%Y%m%dT%H%M%S')}.SAFE"

        return (processing_condition, creation_date, tile_name, measurement_day, input_path, mission),

    return _create_random_input_example

@pytest.fixture(scope='function')
def get_path_input_example(
    ):
    '''
    get_path_input_example Fixture function return the path of the input_example tuple


    :return: the input path 
    :rtype: str
    '''
    def _extract_path(input_tuple: tuple[tuple]) -> tuple[tuple]:
        return tuple((input[4],) for input in input_tuple)

    return _extract_path

@pytest.fixture(scope='function')
def get_wekeo_api_data(
    ):
    '''
    get_wekeo_api_data Fixture function return the wekeo api data example per page write in config_test 


    :return: the dictionary of all the data on a page of wekeo api
    :rtype: dict
    '''
    def _get_page_data(page_name: int) -> dict:

        with open('test/HRWSI_System/harvester/config_test.yaml', 'r', encoding="utf-8") as config_file:
            file_data = yaml.safe_load(config_file)

        return file_data[f"wekeo_api_data_page_{page_name}"]

    return _get_page_data
