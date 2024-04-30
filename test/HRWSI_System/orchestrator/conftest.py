import os
import sys
import random
import uuid
import yaml
import pytest
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.apimanager.artificial_data_for_database.create_input import random_date

@pytest.fixture(scope='function')
def get_processing_task_example():
    '''
    get_processing_task_example Fixture function return a random processing task tuple example  


    :return: a processing_task tuple
    :rtype: tuple
    '''
    def _create_random_processing_task_example() -> tuple[tuple]:
        with open('test/HRWSI_System/harvester/config_test.yaml', 'r', encoding="utf-8") as config_file:
            file_data = yaml.safe_load(config_file)

        start_date = file_data["start_date"]
        end_date = file_data["end_date"]

        creation_date = random_date(start_date=start_date, end_date=end_date, datetime_format='%Y-%m-%d %H:%M:%S')
        input_fk_id = random.randint(0, 100)
        has_ended = False
        preceding_input_id = random.randint(0, 100)
        virtual_machine_id = uuid.uuid1()

        return (input_fk_id, virtual_machine_id, creation_date, preceding_input_id, has_ended),

    return _create_random_processing_task_example

@pytest.fixture(scope='function')
def get_input_id_form_processing_task_example(
    ):
    '''
    get_input_id_form_processing_task_example Fixture function return the input_fk_id of the processing_task example tuple


    :return: the input id 
    :rtype: int
    '''
    def _extract_input_id(pt_tuple: tuple[tuple]) -> tuple[tuple]:
        return tuple((input[0],) for input in pt_tuple)

    return _extract_input_id
