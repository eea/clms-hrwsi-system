"""Tests for check_all_processing_tasks_has_not_ended."""
import os
import sys
# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('hrwsi_watqual_sys')[:-1])
sys.path.append(ROOT_FOLDER+'hrwsi_watqual_sys')

from HRWSI_System.launcher.launcher import Launcher
from HRWSI_System.harvester.apimanager.hrwsi_database_api_manager import HRWSIDatabaseApiManager

def test_all_processing_tasks_are_finished(
        mocker):
    '''
    Scenario :

    - All the processing tasks are finished

    Expected behaviour:

    - Stop the Launcher workflow
    '''

    cursor = [{'count': '0'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_all_processing_tasks_has_not_ended
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    launcher = Launcher()

    expected = False
    actual = launcher.check_all_processing_tasks_has_not_ended(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once

def test_all_processing_tasks_are_not_finished(
        mocker):
    '''
    Scenario :

    - All the processing tasks aren't finished

    Expected behaviour:

    - Continue the Launcher workflow
    '''

    cursor = [{'count': '1'}]

    # Use a mocker to simulate the result of execute_request_in_database function in check_all_processing_tasks_has_not_ended
    get_product_data_type_list_in_database_mock = mocker.patch.object(
        HRWSIDatabaseApiManager,
        'execute_request_in_database',
        return_value = cursor
    )

    launcher = Launcher()

    expected = True
    actual = launcher.check_all_processing_tasks_has_not_ended(cur=())

    assert expected == actual
    assert get_product_data_type_list_in_database_mock.assert_called_once
