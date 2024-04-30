"""Tests for check_running_processing_tasks_product_can_create_input."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.harvester.harvester import Harvester
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def test_with_empty_input_type_list(
        mocker):
    '''
    Scenario :

    - The input_type_list is empty

    Expected behaviour:

    - Stop the Harvester workflow
    '''

    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': 'L2A'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = []

    expected = False
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_with_empty_product_type_list(
        mocker):
    '''
    Scenario :

    - The product_data_type_list is empty ie all processing_tasks are ended

    Expected behaviour:

    - Stop the Harvester workflow
    '''

    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': '[]'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = ["L2A"]

    expected = False
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_with_some_input_type_in_product_type_list(
        mocker):
    '''
    Scenario :

    - Some input type list are in product of running processing tasks

    Expected behaviour:

    - Continue the Harvester workflow
    '''

    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': 'L2A'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = ["L1C","L2A"]

    expected = True
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_with_some_product_type_in_input_type_list(
        mocker):
    '''
    Scenario :

    - Some product of running processing tasks are in input type list

    Expected behaviour:

    - Continue the Harvester workflow
    '''

    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': 'L1C'},
              {'get_product_data_type_of_processing_tasks_not_ended':'L2A'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = ["L2A"]

    expected = True
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_with_all_product_type_in_input_type_list(
        mocker):
    '''
    Scenario :

    - All product of running processing tasks are in input type list

    Expected behaviour:

    - Continue the Harvester workflow
    '''

    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': 'L2A'},
              {'get_product_data_type_of_processing_tasks_not_ended': 'L1C'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = ["L1C","L2A"]

    expected = True
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_without_product_type_in_input_type_list(
        mocker):
    '''
    Scenario :

    - All product of running processing tasks aren't in input type list

    Expected behaviour:

    - Stop the Harvester workflow
    '''
    cursor = [{'get_product_data_type_of_processing_tasks_not_ended': 'L2B, L2C'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_running_processing_tasks_product_can_create_input
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    harvester = Harvester()
    harvester.input_type_list = ["L1C","L2A"]

    expected = False
    actual = harvester.check_running_processing_tasks_product_can_create_input(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once
